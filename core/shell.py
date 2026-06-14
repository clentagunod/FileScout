"""
shell.py — Interactive terminal shell for FileScout.
Accepts commands typed by the user during a session.
"""

import threading
from pathlib import Path

from core.config import get_active_rules, get_duplicate_config, get_ignore_config, get_rename_config, get_poll_interval
from core.organizer import scan_and_organize
from core.watcher import DirectoryWatcher
from utils.logger import get_logger

# ─── MACROS ───────────────────────────────────────────────────────────────────
BANNER_WIDTH    = 58
DIVIDER_CHAR    = "─"
PROMPT_COLOR    = "\033[96m"
RESET           = "\033[0m"
BOLD            = "\033[1m"
GREEN           = "\033[92m"
YELLOW          = "\033[93m"
RED             = "\033[91m"
GREY            = "\033[90m"
# ──────────────────────────────────────────────────────────────────────────────


def _divider(char=DIVIDER_CHAR, width=BANNER_WIDTH) -> str:
    return GREY + char * width + RESET


def _banner(app_name: str, version: str):
    print(_divider("═"))
    print(f"{BOLD}{'  ' + app_name:^{BANNER_WIDTH}}{RESET}")
    print(f"{GREY}{'Automatic File Organizer  v' + version:^{BANNER_WIDTH}}{RESET}")
    print(_divider("═"))
    print()


def _help(app_name: str):
    name_lower = app_name.lower()
    print(_divider())
    print(f"  {BOLD}Available Commands{RESET}")
    print(_divider())
    cmds = [
        (f"start {name_lower} <path>", "Begin watching a directory"),
        (f"scan  {name_lower} <path>", "One-time scan and organize"),
        ("status",                      "Show current watcher status"),
        ("rules",                       "List active file-type rules"),
        ("stop",                        "Stop the active watcher"),
        ("help",                        "Show this help message"),
        ("exit / quit",                 "Exit FileScout"),
    ]
    for cmd, desc in cmds:
        print(f"  {YELLOW}{cmd:<30}{RESET}  {desc}")
    print(_divider())
    print()


def _print_rules(rules: list):
    print(_divider())
    print(f"  {BOLD}Active Rules{RESET}")
    print(_divider())
    for rule in rules:
        exts = "  ".join(rule["extensions"])
        print(f"  {GREEN}{rule['destination_folder']:<18}{RESET}  {GREY}{exts}{RESET}")
    print(_divider())
    print()


class FileScoutShell:
    """
    Interactive REPL shell that manages watcher lifecycle
    and dispatches user commands.
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.app_name = settings["app"]["name"]
        self.version  = settings["app"].get("version", "1.0.0")
        self.prompt   = settings["app"].get("prompt_symbol", ">>")
        self.log      = get_logger(self.app_name)

        self._watcher: DirectoryWatcher | None = None
        self._watcher_thread: threading.Thread | None = None

    # ── Public entry point ───────────────────────────────────────────────────

    def run(self, auto_start_path: str | None = None):
        """
        Start the interactive shell.
        If auto_start_path is provided, immediately begin watching that path.
        """
        _banner(self.app_name, self.version)
        _help(self.app_name)

        if auto_start_path:
            self._cmd_start(auto_start_path)

        while True:
            try:
                raw = input(
                    f"{PROMPT_COLOR}{self.app_name}{RESET} "
                    f"{GREY}{self.prompt}{RESET} "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._cmd_stop()
                print(f"\n{GREY}Goodbye.{RESET}\n")
                break

            if not raw:
                continue

            parts = raw.split()
            cmd   = parts[0].lower()

            if cmd in ("exit", "quit"):
                self._cmd_stop()
                print(f"\n{GREY}Goodbye.{RESET}\n")
                break
            elif cmd == "help":
                _help(self.app_name)
            elif cmd == "status":
                self._cmd_status()
            elif cmd == "rules":
                _print_rules(get_active_rules(self.settings))
            elif cmd == "stop":
                self._cmd_stop()
            elif cmd == "start":
                self._handle_start(parts)
            elif cmd == "scan":
                self._handle_scan(parts)
            else:
                print(f"  {RED}Unknown command:{RESET} '{cmd}'  — type {YELLOW}help{RESET} for commands.\n")

    # ── Command handlers ─────────────────────────────────────────────────────

    def _handle_start(self, parts: list):
        """Parse 'start <appname> <path>' or 'start <path>'."""
        path_arg = self._extract_path(parts)
        if path_arg is None:
            print(f"  {RED}Usage:{RESET}  start {self.app_name.lower()} <directory>\n")
            return
        self._cmd_start(path_arg)

    def _handle_scan(self, parts: list):
        """Parse 'scan <appname> <path>' or 'scan <path>'."""
        path_arg = self._extract_path(parts)
        if path_arg is None:
            print(f"  {RED}Usage:{RESET}  scan {self.app_name.lower()} <directory>\n")
            return
        self._cmd_scan(path_arg)

    def _extract_path(self, parts: list) -> str | None:
        """
        Extract path from a command like:
          start filescout C:/Users/Clent/Downloads
          start C:/Users/Clent/Downloads
        """
        if len(parts) < 2:
            return None
        # If second token matches the app name (case-insensitive), path is third token
        if parts[1].lower() == self.app_name.lower():
            return " ".join(parts[2:]) if len(parts) > 2 else None
        # Otherwise path starts at second token
        return " ".join(parts[1:])

    def _cmd_start(self, path_str: str):
        """Start the directory watcher."""
        watch_dir = Path(path_str).expanduser().resolve()

        if not watch_dir.exists():
            print(f"  {RED}Directory not found:{RESET} {watch_dir}\n")
            return

        if not watch_dir.is_dir():
            print(f"  {RED}Path is not a directory:{RESET} {watch_dir}\n")
            return

        if self._watcher and self._watcher._running:
            print(f"  {YELLOW}A watcher is already active.{RESET} Run {YELLOW}stop{RESET} first.\n")
            return

        rules     = get_active_rules(self.settings)
        rename    = get_rename_config(self.settings)
        ignore    = get_ignore_config(self.settings)
        dup       = get_duplicate_config(self.settings)
        interval  = get_poll_interval(self.settings)

        # Run an immediate scan before starting the live watch
        self.log.info("Running initial scan before starting watcher...")
        scan_and_organize(watch_dir, rules, rename, ignore, dup, self.app_name)

        self._watcher = DirectoryWatcher(
            watch_dir=watch_dir,
            rules=rules,
            rename_cfg=rename,
            ignore_cfg=ignore,
            dup_cfg=dup,
            poll_interval=interval,
            app_name=self.app_name,
        )

        self._watcher_thread = threading.Thread(
            target=self._watcher.start,
            daemon=True,
            name="FileScout-Watcher",
        )
        self._watcher_thread.start()

    def _cmd_scan(self, path_str: str):
        """One-time scan without starting continuous watch."""
        watch_dir = Path(path_str).expanduser().resolve()

        if not watch_dir.exists() or not watch_dir.is_dir():
            print(f"  {RED}Invalid directory:{RESET} {watch_dir}\n")
            return

        rules  = get_active_rules(self.settings)
        rename = get_rename_config(self.settings)
        ignore = get_ignore_config(self.settings)
        dup    = get_duplicate_config(self.settings)

        scan_and_organize(watch_dir, rules, rename, ignore, dup, self.app_name)

    def _cmd_stop(self):
        if self._watcher and self._watcher._running:
            self._watcher.stop()
            self._watcher = None
        else:
            print(f"  {GREY}No active watcher to stop.{RESET}\n")

    def _cmd_status(self):
        print(_divider())
        print(f"  {BOLD}Status{RESET}")
        print(_divider())
        if self._watcher and self._watcher._running:
            print(f"  Watcher  {GREEN}● ACTIVE{RESET}")
            print(f"  Path     {YELLOW}{self._watcher.watch_dir}{RESET}")
            print(f"  Interval {self._watcher.poll_interval}s")
        else:
            print(f"  Watcher  {RED}○ INACTIVE{RESET}")
        print(_divider())
        print()