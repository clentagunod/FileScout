"""
main.py — Entry point for FileScout.

Usage:
    python main.py
    python main.py start filescout "C:/Users/Clent/Downloads"
    python main.py scan  filescout "C:/Users/Clent/Downloads"

When run with no arguments, FileScout opens an interactive terminal shell.
When run with arguments, it pre-fills the command and then enters the shell.
"""

import sys
import os
import time

# ── Make sure project root is on the path (so sub-modules resolve) ────────────
sys.path.insert(0, os.path.dirname(__file__))

from core.config import load_settings, get_app_name
from core.shell import FileScoutShell
from utils.logger import setup_logger

# ── MACROS — Edit these to change global behavior ─────────────────────────────
DEFAULT_SETTINGS_PATH   = "settings.json"   # Relative to main.py
EXIT_CODE_BAD_SETTINGS  = 2
# ──────────────────────────────────────────────────────────────────────────────


def main():
    # 1. Load settings
    try:
        settings = load_settings()
    except (FileNotFoundError, ValueError) as e:
        print(f"\n  [ERROR] {e}\n")
        sys.exit(EXIT_CODE_BAD_SETTINGS)

    app_name = get_app_name(settings)

    # 2. Boot logger
    setup_logger(
        app_name=app_name,
        log_to_file=settings["app"].get("log_to_file", True),
        log_filename=settings["app"].get("log_filename", "filescout.log"),
    )

    # 3. Parse optional CLI arguments
    #    Supports:  python main.py start filescout "C:/some/path"
    #               python main.py scan  filescout "C:/some/path"
    auto_command: str | None = None

    if len(sys.argv) >= 2:
        # Reconstruct the command as if it was typed in the shell
        auto_command = " ".join(sys.argv[1:])

    # 4. Launch interactive shell
    shell = FileScoutShell(settings)
    shell.run(auto_start_path=_extract_auto_path(auto_command, app_name))


def _extract_auto_path(auto_command: str | None, app_name: str) -> str | None:
    """
    If the user ran:  python main.py start filescout C:/Downloads
    We want to auto-start watching C:/Downloads.
    Returns the path string, or None if no valid start command.
    """
    if not auto_command:
        return None

    parts = auto_command.split()
    verb  = parts[0].lower() if parts else ""

    if verb not in ("start",):
        # For 'scan' and others, let the shell handle them interactively
        return None

    # Strip verb (and optional app name) to get the path
    if len(parts) >= 3 and parts[1].lower() == app_name.lower():
        return " ".join(parts[2:])
    elif len(parts) >= 2:
        return " ".join(parts[1:])

    return None


if __name__ == "__main__":
    main()
