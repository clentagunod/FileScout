"""
logger.py — Logging setup for FileScout.
Outputs to console (with color) and optionally to a log file.
"""

import logging
import sys
from pathlib import Path


# ANSI color codes for terminal output
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    GREY    = "\033[90m"
    WHITE   = "\033[97m"


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG:    Colors.GREY,
        logging.INFO:     Colors.WHITE,
        logging.WARNING:  Colors.YELLOW,
        logging.ERROR:    Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        levelname = f"{color}[{record.levelname:<8}]{Colors.RESET}"
        time_str = f"{Colors.GREY}{self.formatTime(record, '%H:%M:%S')}{Colors.RESET}"
        message = record.getMessage()
        return f"{time_str} {levelname} {message}"


def setup_logger(app_name: str, log_to_file: bool = True, log_filename: str = "filescout.log") -> logging.Logger:
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler (colored)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ColorFormatter())
    logger.addHandler(ch)

    # File handler (plain)
    if log_to_file:
        log_path = Path(__file__).parent.parent / log_filename
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

    return logger


def get_logger(app_name: str = "FileScout") -> logging.Logger:
    """Retrieve the already-configured logger by name."""
    return logging.getLogger(app_name)