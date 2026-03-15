"""
platform/windows/paths.py

All Windows-specific paths used by cleaners.
Core cleaners call get_temp_paths() etc. — never hardcode paths in core/.

Uses os.environ to resolve user-specific folders so it works
correctly for any Windows user account.
"""

import os
from utils.logger import get_logger

logger = get_logger(__name__)


def _env(var: str, fallback: str = "") -> str:
    """Safely read an environment variable."""
    return os.environ.get(var, fallback)


def get_temp_paths() -> list[str]:
    """
    Returns all standard Windows temp folder paths.
    These are safe to scan and delete from.
    """
    paths = [
        # System temp
        r"C:\Windows\Temp",

        # User temp (%TEMP% / %TMP% both point here usually)
        _env("TEMP"),
        _env("TMP"),

        # Windows prefetch — safe to clear, Windows rebuilds it
        r"C:\Windows\Prefetch",

        # Old Windows Update leftovers
        r"C:\Windows\SoftwareDistribution\Download",

        # Windows error reporting cache
        os.path.join(_env("LOCALAPPDATA"), r"Microsoft\Windows\WER\ReportQueue"),
        os.path.join(_env("LOCALAPPDATA"), r"Microsoft\Windows\WER\ReportArchive"),

        # Thumbnail cache
        os.path.join(
            _env("LOCALAPPDATA"),
            r"Microsoft\Windows\Explorer"
        ),

        # Temporary internet files (legacy IE/Edge)
        os.path.join(
            _env("LOCALAPPDATA"),
            r"Microsoft\Windows\INetCache"
        ),

        # Windows Installer patch cache
        os.path.join(_env("WINDIR", r"C:\Windows"), "Installer", "$PatchCache$"),
    ]

    # Deduplicate and filter out empty / non-existent paths
    seen = set()
    valid = []
    for p in paths:
        if not p:
            continue
        p = os.path.normpath(p)
        if p in seen:
            continue
        seen.add(p)
        if os.path.exists(p):
            valid.append(p)
        else:
            logger.debug(f"Path does not exist, skipping: {p}")

    logger.debug(f"Resolved {len(valid)} temp paths")
    return valid


def get_browser_cache_paths() -> dict[str, list[str]]:
    """
    Returns cache paths grouped by browser name.
    Used by the browser cache cleaner (Phase 2).
    """
    local = _env("LOCALAPPDATA")
    appdata = _env("APPDATA")

    return {
        "Chrome": [
            os.path.join(local, r"Google\Chrome\User Data\Default\Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\Code Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\GPUCache"),
        ],
        "Edge": [
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Code Cache"),
            os.path.join(local, r"Microsoft\Edge\User Data\Default\GPUCache"),
        ],
        "Firefox": [
            os.path.join(local, r"Mozilla\Firefox\Profiles"),  # needs profile scan
        ],
        "Opera": [
            os.path.join(appdata, r"Opera Software\Opera Stable\Cache"),
        ],
        "Brave": [
            os.path.join(local, r"BraveSoftware\Brave-Browser\User Data\Default\Cache"),
        ],
    }


def get_recycle_bin_path() -> str:
    """Returns the primary recycle bin path for the C: drive."""
    return r"C:\$Recycle.Bin"