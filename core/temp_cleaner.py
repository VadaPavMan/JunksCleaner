"""
core/temp_cleaner.py

TempCleaner — scans and cleans Windows temporary file folders.

Targets:
  - C:\\Windows\\Temp
  - %TEMP% / %TMP%  (user temp)
  - C:\\Windows\\Prefetch
  - C:\\Windows\\SoftwareDistribution\\Download
  - Windows Error Reporting cache
  - INetCache (legacy IE/Edge)

Inherits scan() and clean() from BaseCleaner.
Only needs to define name, description, and scan_paths.
"""

from core.base_cleaner import BaseCleaner
from os_platform.detector import is_windows
from utils.logger import get_logger

logger = get_logger(__name__)


class TempCleaner(BaseCleaner):

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Temp File Cleaner"

    @property
    def description(self) -> str:
        return (
            "Removes temporary files left behind by Windows and "
            "installed applications. Safe to clean at any time."
        )

    # ── Paths ─────────────────────────────────────────────────────────────────

    @property
    def scan_paths(self) -> list[str]:
        """
        Resolved at call time.
        Returns only paths that exist on the current machine.
        """
        if is_windows():
            from os_platform.windows.paths import get_temp_paths
            return get_temp_paths()
        else:
            # Linux placeholder — Phase 7
            from os_platform.linux.paths import get_temp_paths as linux_temp
            return linux_temp()

    # ── Optional overrides ────────────────────────────────────────────────────
    # scan() and clean() from BaseCleaner work perfectly for temp files.
    # No need to override them here.
    #
    # If you ever need custom scan logic (e.g. filter by extension,
    # skip files newer than N days), override scan() here and call
    # super().scan() then filter result.entries.

    def scan_filtered(
        self,
        min_age_days: int = 0,
        extensions: list[str] = None,
        cancel_event=None,
        on_progress=None,
    ):
        """
        Optional filtered scan — only returns files matching criteria.

        min_age_days:  skip files modified within the last N days
        extensions:    if provided, only include files with these extensions
                       e.g. [".tmp", ".log", ".bak"]
        """
        import os
        import time

        base_result = self.scan(cancel_event=cancel_event, on_progress=on_progress)

        if min_age_days <= 0 and not extensions:
            return base_result   # no filter needed

        now = time.time()
        cutoff = now - (min_age_days * 86400)

        filtered_entries = []
        filtered_bytes   = 0

        for entry in base_result.entries:
            # Age filter
            if min_age_days > 0:
                try:
                    mtime = os.path.getmtime(entry.path)
                    if mtime > cutoff:
                        continue   # too recent
                except OSError:
                    pass

            # Extension filter
            if extensions:
                ext = os.path.splitext(entry.path)[1].lower()
                if ext not in [e.lower() for e in extensions]:
                    continue

            filtered_entries.append(entry)
            filtered_bytes += entry.size_bytes

        base_result.entries     = filtered_entries
        base_result.total_bytes = filtered_bytes

        logger.info(
            f"Filtered scan: {len(filtered_entries)} files "
            f"(from {base_result.total_files + len(base_result.entries)} original)"
        )
        return base_result