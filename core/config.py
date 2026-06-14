"""
config.py — Loads and validates settings.json for FileScout.
"""

import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"


def load_settings() -> dict:
    """Load settings from settings.json. Returns parsed dict."""
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(
            f"Settings file not found at: {SETTINGS_FILE}\n"
            "Please ensure settings.json exists in the FileScout directory."
        )
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
    _validate(settings)
    return settings


def _validate(settings: dict):
    """Basic validation of required fields."""
    required_top = ["app", "rename", "rules", "ignore", "duplicate_handling"]
    for key in required_top:
        if key not in settings:
            raise ValueError(f"settings.json is missing required section: '{key}'")

    for rule in settings.get("rules", []):
        for field in ["name", "extensions", "destination_folder", "enabled"]:
            if field not in rule:
                raise ValueError(
                    f"Rule '{rule.get('name', '?')}' is missing field: '{field}'"
                )


def get_app_name(settings: dict) -> str:
    return settings["app"].get("name", "FileScout")


def get_poll_interval(settings: dict) -> int:
    return int(settings["app"].get("poll_interval_seconds", 3))


def get_active_rules(settings: dict) -> list:
    return [r for r in settings["rules"] if r.get("enabled", True)]


def get_ignore_config(settings: dict) -> dict:
    return settings.get("ignore", {})


def get_rename_config(settings: dict) -> dict:
    return settings.get("rename", {})


def get_duplicate_config(settings: dict) -> dict:
    return settings.get("duplicate_handling", {})