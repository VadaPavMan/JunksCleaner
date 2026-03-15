"""
platform/detector.py

Detects the current OS and version.
All platform-specific code branches through here.

Usage:
    from os_platform.detector import get_platform, Platform

    if get_platform() == Platform.WINDOWS:
        from os_platform.windows.paths import get_temp_paths
    elif get_platform() == Platform.LINUX:
        from os_platform.linux.paths import get_temp_paths
"""

import sys
import platform as _platform
from enum import Enum, auto
from utils.logger import get_logger

logger = get_logger(__name__)


class Platform(Enum):
    WINDOWS = auto()
    LINUX   = auto()
    MACOS   = auto()
    UNKNOWN = auto()


def get_platform() -> Platform:
    """Detect and return the current operating system."""
    system = sys.platform

    if system.startswith("win"):
        return Platform.WINDOWS
    elif system.startswith("linux"):
        return Platform.LINUX
    elif system.startswith("darwin"):
        return Platform.MACOS
    else:
        return Platform.UNKNOWN


def get_os_version() -> str:
    """Returns a human-readable OS version string."""
    try:
        return _platform.platform()
    except Exception:
        return "Unknown"


def is_windows() -> bool:
    return get_platform() == Platform.WINDOWS


def is_linux() -> bool:
    return get_platform() == Platform.LINUX


# Log the platform on import
_detected = get_platform()
logger.info(f"Platform detected: {_detected.name} — {get_os_version()}")