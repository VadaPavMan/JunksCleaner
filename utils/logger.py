"""
utils/logger.py

Central logging setup for JunksCleaner.
Call get_logger(__name__) in every module to get a named logger.

Log levels:
  DEBUG    — detailed internal info (dev only)
  INFO     — general events (start, scan done, files deleted)
  WARNING  — something unexpected but recoverable
  ERROR    — an operation failed but the app continues
  CRITICAL — app cannot continue
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ── Config ────────────────────────────────────────────────────────────────────

_THIS_FILE   = os.path.abspath(__file__)             # .../utils/logger.py
_UTILS_DIR   = os.path.dirname(_THIS_FILE)           # .../utils/
_PROJECT_ROOT = os.path.dirname(_UTILS_DIR)          # .../JunksCleaner/
LOG_DIR  = os.path.join(_PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "junkscleaner.log")

# Max 2 MB per log file, keep last 3 files
MAX_BYTES   = 2 * 1024 * 1024
BACKUP_COUNT = 3

LOG_FORMAT  = "[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Internal state ────────────────────────────────────────────────────────────

_initialized = False


def _setup_logging():
    """Run once — configures root logger with file + console handlers."""
    global _initialized
    if _initialized:
        return

    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler — rotating, keeps history
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler — INFO and above only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Scan started")
    """
    _setup_logging()
    return logging.getLogger(name)