"""
core/base_cleaner.py

BaseCleaner — abstract base class every cleaner module inherits from.

Enforces a consistent interface across all cleaners:
    scan()   → finds files, returns ScanResult
    clean()  → deletes selected files, returns CleanResult

Cleaners must NOT import from ui/ — they return plain data objects
and the UI layer decides how to display them.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import threading
from app.state import ScanResult, FileEntry
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Result type returned by clean() ──────────────────────────────────────────

@dataclass
class CleanResult:
    files_deleted:  int = 0
    files_skipped:  int = 0
    bytes_freed:    int = 0
    errors:         list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def partial(self) -> bool:
        """True if some files were deleted and some skipped."""
        return self.files_deleted > 0 and self.files_skipped > 0


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseCleaner(ABC):
    """
    All cleaner modules inherit from this.

    Subclass contract:
        - Override scan_paths property to return the list of paths to scan
        - Override name property to return a display name
        - Optionally override scan() or clean() for custom behavior
    """

    def __init__(self):
        self._logger = get_logger(self.__class__.__name__)

    # ── Properties subclasses must define ─────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name, e.g. 'Temp File Cleaner'"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description shown in the UI."""
        ...

    @property
    @abstractmethod
    def scan_paths(self) -> list[str]:
        """
        List of directory paths this cleaner will scan.
        Resolved at call time (not at import) so env vars are current.
        """
        ...

    # ── Core interface ────────────────────────────────────────────────────────

    def scan(
        self,
        cancel_event: Optional[threading.Event] = None,
        on_progress=None,   # optional callback(current, total)
    ) -> ScanResult:
        """
        Walk all scan_paths, collect file entries.
        Returns a ScanResult with all found files.

        cancel_event: set this threading.Event to abort mid-scan.
        on_progress:  called with (files_found_so_far, current_path)
                      use this to update a progress bar.
        """
        import os
        from utils.file_utils import get_file_info

        result = ScanResult()
        self._logger.info(f"[{self.name}] Scan started — {len(self.scan_paths)} paths")

        for folder in self.scan_paths:
            if cancel_event and cancel_event.is_set():
                self._logger.info("Scan cancelled")
                break

            if not os.path.exists(folder):
                self._logger.debug(f"Path not found, skipping: {folder}")
                continue

            self._logger.debug(f"Scanning: {folder}")

            try:
                for dirpath, dirnames, filenames in os.walk(folder):
                    if cancel_event and cancel_event.is_set():
                        break

                    for fname in filenames:
                        if cancel_event and cancel_event.is_set():
                            break

                        fpath = os.path.join(dirpath, fname)
                        info = get_file_info(fpath)

                        if info is None:
                            continue   # couldn't stat — skip silently

                        entry = FileEntry(
                            path=fpath,
                            size_bytes=info["size_bytes"],
                            modified=info["modified"],
                            selected=True,
                        )
                        result.entries.append(entry)
                        result.total_bytes += info["size_bytes"]

                        if on_progress:
                            on_progress(len(result.entries), fpath)

            except PermissionError:
                msg = f"Permission denied: {folder}"
                self._logger.warning(msg)
                result.error = msg
            except Exception as e:
                msg = f"Error scanning {folder}: {e}"
                self._logger.error(msg)
                result.error = msg

        self._logger.info(
            f"[{self.name}] Scan done — "
            f"{result.total_files} files, "
            f"{result.total_bytes} bytes"
        )
        return result

    def clean(
        self,
        scan_result: ScanResult,
        cancel_event: Optional[threading.Event] = None,
        on_progress=None,   # optional callback(deleted_so_far, total_selected)
    ) -> CleanResult:
        """
        Delete all selected files from a previous scan result.

        Only deletes entries where entry.selected == True.
        Skips locked or inaccessible files gracefully.
        """
        from utils.file_utils import safe_delete_file

        result     = CleanResult()
        to_delete  = scan_result.selected_files
        total      = len(to_delete)

        self._logger.info(f"[{self.name}] Clean started — {total} files selected")

        for i, entry in enumerate(to_delete):
            if cancel_event and cancel_event.is_set():
                self._logger.info("Clean cancelled by user")
                break

            ok, reason = safe_delete_file(entry.path)

            if ok:
                result.files_deleted += 1
                result.bytes_freed   += entry.size_bytes
            else:
                result.files_skipped += 1
                result.errors.append(f"{entry.path}: {reason}")

            if on_progress:
                on_progress(i + 1, total)

        self._logger.info(
            f"[{self.name}] Clean done — "
            f"{result.files_deleted} deleted, "
            f"{result.files_skipped} skipped, "
            f"{result.bytes_freed} bytes freed"
        )
        return result