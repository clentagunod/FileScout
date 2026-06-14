"""
watcher.py — Polls a directory for new files and triggers the organizer.
Uses a polling approach so no external dependencies are required.
"""

import time
from pathlib import Path

from core.organizer import process_file
from utils.logger import get_logger


class DirectoryWatcher:
    """
    Monitors a directory at a configurable interval.
    Detects new files (not present in the previous scan snapshot)
    and routes them through the organizer.
    """

    def __init__(
        self,
        watch_dir: Path,
        rules: list,
        rename_cfg: dict,
        ignore_cfg: dict,
        dup_cfg: dict,
        poll_interval: int = 3,
        app_name: str = "FileScout",
    ):
        self.watch_dir = watch_dir
        self.rules = rules
        self.rename_cfg = rename_cfg
        self.ignore_cfg = ignore_cfg
        self.dup_cfg = dup_cfg
        self.poll_interval = poll_interval
        self.app_name = app_name
        self.log = get_logger(app_name)
        self._running = False
        self._known_files: set = set()

    def _snapshot(self) -> set:
        """Return the set of file paths currently in the watch directory (top-level only)."""
        try:
            return {f for f in self.watch_dir.iterdir() if f.is_file()}
        except Exception as e:
            self.log.error(f"Could not read watch directory: {e}")
            return set()

    def start(self):
        """Begin the polling loop. Blocks until stop() is called."""
        self._running = True
        self._known_files = self._snapshot()

        self.log.info(
            f"Watching: \033[96m{self.watch_dir}\033[0m  "
            f"(interval: {self.poll_interval}s)"
        )
        self.log.info("Press \033[93mCtrl+C\033[0m or type \033[93mstop\033[0m to stop watching.\n")

        try:
            while self._running:
                time.sleep(self.poll_interval)
                self._tick()
        except KeyboardInterrupt:
            self.stop()

    def _tick(self):
        """One poll cycle — detect new files and process them."""
        current = self._snapshot()
        new_files = current - self._known_files

        for f in new_files:
            self.log.info(f"Detected new file: \033[95m{f.name}\033[0m")
            process_file(
                f,
                self.watch_dir,
                self.rules,
                self.rename_cfg,
                self.ignore_cfg,
                self.dup_cfg,
                self.app_name,
            )

        # Refresh snapshot (files may have moved)
        self._known_files = self._snapshot()

    def stop(self):
        """Stop the polling loop gracefully."""
        self._running = False
        self.log.info("Watcher stopped.")