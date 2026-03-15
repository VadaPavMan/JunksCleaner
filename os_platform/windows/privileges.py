"""
platform/windows/privileges.py

Admin privilege detection and UAC elevation request.

Some temp folders (C:\\Windows\\Temp, Prefetch) require admin rights.
Call is_admin() before attempting those paths.
Call request_elevation() to relaunch the app as admin via UAC prompt.
"""

import os
import sys
import ctypes
from utils.logger import get_logger

logger = get_logger(__name__)


def is_admin() -> bool:
    """
    Returns True if the current process has Windows admin privileges.
    Always returns False on non-Windows platforms.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Not on Windows
        return False
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        return False


def request_elevation():
    """
    Relaunch the current script with UAC elevation (admin rights).
    This triggers the Windows "Do you want to allow this app to make
    changes?" dialog. The current process exits after relaunching.

    Call this only when the user explicitly requests an action that
    needs admin rights — never on startup automatically.
    """
    if is_admin():
        logger.debug("Already running as admin, no elevation needed")
        return

    logger.info("Requesting UAC elevation — relaunching as admin")
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # verb — triggers UAC
            sys.executable, # the python executable
            " ".join(sys.argv),  # original arguments
            None,           # working directory
            1,              # SW_NORMAL
        )
        sys.exit(0)   # exit current non-admin process
    except Exception as e:
        logger.error(f"Elevation request failed: {e}")


def get_privilege_level() -> str:
    """Human-readable privilege level for display in the UI."""
    return "Administrator" if is_admin() else "Standard User"