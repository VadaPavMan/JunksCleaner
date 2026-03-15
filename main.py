"""
JunksCleaner — main entry point
Run this file to launch the application.
"""

import sys
import os

# ── MUST be the very first thing before any project imports ──────────────────
# Resolves the absolute path of this file's directory (the project root)
# and inserts it at position 0 in sys.path.
# This fixes "ModuleNotFoundError: No module named 'config'" when running
# from any working directory, including OneDrive paths on Windows.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from utils.logger import get_logger
from app.app import JunksCleanerApp

logger = get_logger(__name__)


def main():
    logger.info("=" * 50)
    logger.info("JunksCleaner starting up")
    logger.info(f"Project root: {_PROJECT_ROOT}")
    logger.info("=" * 50)

    try:
        app = JunksCleanerApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("JunksCleaner shut down cleanly")


if __name__ == "__main__":
    main()