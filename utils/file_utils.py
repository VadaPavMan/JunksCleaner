"""
utils/file_utils.py

File operation helpers used by all cleaners.

  format_size(bytes)     → "1.23 MB"
  safe_delete(path)      → True/False, never raises
  get_file_info(path)    → dict with size, modified date
  is_locked(path)        → True if another process holds the file
"""

import os
import stat
import datetime
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Size formatting ───────────────────────────────────────────────────────────

def format_size(size_bytes: int) -> str:
    """
    Convert raw byte count to a human-readable string.

    Examples:
        format_size(0)          → "0 B"
        format_size(1024)       → "1.00 KB"
        format_size(1048576)    → "1.00 MB"
        format_size(1073741824) → "1.00 GB"
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)

    for unit in units[:-1]:
        if size < 1024.0:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0

    return f"{size:.2f} {units[-1]}"


# ── Date formatting ───────────────────────────────────────────────────────────

def format_modified(timestamp: float) -> str:
    """Convert a file modification timestamp to a readable date string."""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d  %H:%M")
    except Exception:
        return "Unknown"


# ── File info ─────────────────────────────────────────────────────────────────

def get_file_info(path: str) -> Optional[dict]:
    """
    Returns a dict with size_bytes and modified for a single file.
    Returns None if the file cannot be stat'd.
    """
    try:
        s = os.stat(path)
        return {
            "size_bytes": s.st_size,
            "modified":   format_modified(s.st_mtime),
        }
    except (OSError, PermissionError) as e:
        logger.debug(f"Cannot stat {path}: {e}")
        return None


def get_folder_size(path: str) -> int:
    """
    Recursively sum the size of all files in a directory.
    Skips files it cannot access.
    """
    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for fname in filenames:
                try:
                    fp = os.path.join(dirpath, fname)
                    total += os.path.getsize(fp)
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError) as e:
        logger.debug(f"Cannot walk {path}: {e}")
    return total


# ── Lock detection ────────────────────────────────────────────────────────────

def is_locked(path: str) -> bool:
    """
    Try to open the file exclusively.
    Returns True if another process is holding it.
    Windows-only check — on Linux always returns False.
    """
    try:
        with open(path, "a"):
            return False
    except (IOError, PermissionError, OSError):
        return True


# ── Safe delete ───────────────────────────────────────────────────────────────

def safe_delete_file(path: str) -> tuple[bool, str]:
    """
    Delete a single file safely.

    Returns:
        (True, "")           — deleted successfully
        (False, reason_str)  — failed, with reason

    Never raises an exception.
    """
    try:
        if not os.path.exists(path):
            return False, "File not found"

        if not os.path.isfile(path):
            return False, "Not a file"

        # Remove read-only attribute if set (common in Windows temp files)
        try:
            os.chmod(path, stat.S_IWRITE)
        except Exception:
            pass

        os.remove(path)
        logger.debug(f"Deleted: {path}")
        return True, ""

    except PermissionError:
        reason = "Permission denied (file may be in use)"
        logger.warning(f"Cannot delete {path}: {reason}")
        return False, reason

    except OSError as e:
        reason = str(e)
        logger.warning(f"Cannot delete {path}: {reason}")
        return False, reason


def safe_delete_folder_contents(path: str, cancel_event=None) -> tuple[int, int, int]:
    """
    Delete all files inside a folder (non-recursive by default).
    Does NOT delete the folder itself — only its contents.

    Returns:
        (deleted_count, skipped_count, freed_bytes)
    """
    deleted = 0
    skipped = 0
    freed   = 0

    if not os.path.isdir(path):
        return 0, 0, 0

    try:
        entries = list(os.scandir(path))
    except PermissionError:
        logger.warning(f"No permission to scan: {path}")
        return 0, 0, 0

    for entry in entries:
        if cancel_event and cancel_event.is_set():
            logger.info("Delete cancelled by user")
            break

        try:
            size = entry.stat().st_size if entry.is_file() else 0

            if entry.is_file(follow_symlinks=False):
                ok, _ = safe_delete_file(entry.path)
                if ok:
                    deleted += 1
                    freed   += size
                else:
                    skipped += 1

            elif entry.is_dir(follow_symlinks=False):
                # Recursively delete subfolder
                import shutil
                try:
                    subfolder_size = get_folder_size(entry.path)
                    shutil.rmtree(entry.path, ignore_errors=True)
                    # Check if it was actually removed
                    if not os.path.exists(entry.path):
                        deleted += 1
                        freed   += subfolder_size
                    else:
                        skipped += 1
                except Exception as e:
                    logger.warning(f"Cannot remove folder {entry.path}: {e}")
                    skipped += 1

        except Exception as e:
            logger.debug(f"Error processing {entry.path}: {e}")
            skipped += 1

    return deleted, skipped, freed