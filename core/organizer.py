"""
organizer.py — Core file classification and moving logic for FileScout.
"""

import shutil
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger


def _build_extension_map(rules: list) -> dict:
    """Build a flat dict of {'.ext': destination_folder} from active rules."""
    ext_map = {}
    for rule in rules:
        folder = rule["destination_folder"]
        for ext in rule["extensions"]:
            ext_map[ext.lower()] = folder
    return ext_map


def _is_ignored(path: Path, ignore_cfg: dict) -> bool:
    """Return True if this file should be skipped."""
    name = path.name

    if ignore_cfg.get("hidden_files", True) and name.startswith("."):
        return True

    ignore_names = ignore_cfg.get("filenames", [])
    if name in ignore_names:
        return True

    temp_exts = ignore_cfg.get("temp_extensions", [])
    if path.suffix.lower() in temp_exts:
        return True

    return False


def _build_new_name(original: Path, rename_cfg: dict) -> str:
    """
    Build the new filename using the date prefix strategy from settings.
    Example: 'report.pdf' → '2025-06-14_report.pdf'
    """
    if not rename_cfg.get("enabled", True):
        return original.name

    date_str = datetime.now().strftime(rename_cfg.get("date_format", "%Y-%m-%d"))
    sep = rename_cfg.get("separator", "_")

    if rename_cfg.get("preserve_original_name", True):
        stem = original.stem
        suffix = original.suffix
        return f"{date_str}{sep}{stem}{suffix}"
    else:
        return f"{date_str}{original.suffix}"


def _resolve_duplicate(dest_path: Path, dup_cfg: dict) -> Path:
    """
    Handle destination path conflicts based on duplicate strategy.
    'rename'    → append (1), (2), etc.
    'skip'      → return None to signal skip
    'overwrite' → return the same path (caller overwrites)
    """
    strategy = dup_cfg.get("strategy", "rename")
    suffix_fmt = dup_cfg.get("suffix_format", "({n})")

    if not dest_path.exists():
        return dest_path

    if strategy == "overwrite":
        return dest_path

    if strategy == "skip":
        return None  # Caller should check for None

    # strategy == "rename"
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    n = 1
    while True:
        tag = suffix_fmt.replace("{n}", str(n))
        candidate = parent / f"{stem}{tag}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def process_file(
    file_path: Path,
    watch_dir: Path,
    rules: list,
    rename_cfg: dict,
    ignore_cfg: dict,
    dup_cfg: dict,
    app_name: str = "FileScout",
) -> bool:
    """
    Classify and move a single file.
    Returns True if moved, False if skipped or errored.
    """
    log = get_logger(app_name)

    if not file_path.is_file():
        return False

    if _is_ignored(file_path, ignore_cfg):
        log.debug(f"Ignored: {file_path.name}")
        return False

    ext_map = _build_extension_map(rules)
    ext = file_path.suffix.lower()
    destination_folder = ext_map.get(ext)

    if not destination_folder:
        log.debug(f"No rule matched for: {file_path.name} (ext={ext})")
        return False

    dest_dir = watch_dir / destination_folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    new_name = _build_new_name(file_path, rename_cfg)
    dest_path = dest_dir / new_name
    dest_path = _resolve_duplicate(dest_path, dup_cfg)

    if dest_path is None:
        log.warning(f"Skipped (duplicate): {file_path.name}")
        return False

    try:
        shutil.move(str(file_path), str(dest_path))
        log.info(
            f"Moved  \033[96m{file_path.name}\033[0m"
            f"  →  \033[92m{destination_folder}/{dest_path.name}\033[0m"
        )
        return True
    except PermissionError:
        log.warning(f"Permission denied (file may be in use): {file_path.name}")
        return False
    except Exception as e:
        log.error(f"Failed to move '{file_path.name}': {e}")
        return False


def scan_and_organize(
    watch_dir: Path,
    rules: list,
    rename_cfg: dict,
    ignore_cfg: dict,
    dup_cfg: dict,
    app_name: str = "FileScout",
) -> int:
    """
    Scan the watch directory and organize all existing files.
    Returns count of files moved.
    """
    log = get_logger(app_name)
    moved = 0

    files = [f for f in watch_dir.iterdir() if f.is_file()]
    if not files:
        log.info("No files found in the watched directory.")
        return 0

    log.info(f"Scanning {len(files)} file(s) in: {watch_dir}")
    for f in files:
        if process_file(f, watch_dir, rules, rename_cfg, ignore_cfg, dup_cfg, app_name):
            moved += 1

    log.info(f"Scan complete. {moved} file(s) organized.")
    return moved