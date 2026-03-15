"""
app/state.py

Global application state — a single source of truth shared across
the UI and core layers.

Rules:
  - UI reads from state to display data
  - Core writes to state after scans/cleans
  - Nobody stores results locally in page classes
  - State never imports from ui/ or core/
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum, auto


# ── Enums ─────────────────────────────────────────────────────────────────────

class ScanStatus(Enum):
    IDLE      = auto()   # nothing happening
    SCANNING  = auto()   # scan in progress
    DONE      = auto()   # scan finished, results ready
    CLEANING  = auto()   # delete in progress
    CANCELLED = auto()   # user cancelled


class Page(Enum):
    """Maps to sidebar nav items."""
    TEMP_FILES    = "Temp Files"
    BROWSER_CACHE = "Browser Cache"
    RECYCLE_BIN   = "Recycle Bin"
    STARTUP       = "Startup Apps"
    SETTINGS      = "Settings"


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class FileEntry:
    """Represents a single file found during a scan."""
    path:        str
    size_bytes:  int
    modified:    str          # formatted date string
    selected:    bool = True  # checked in the results table by default


@dataclass
class ScanResult:
    """Results from one scan operation."""
    entries:      List[FileEntry] = field(default_factory=list)
    total_bytes:  int = 0
    error:        Optional[str] = None

    @property
    def total_files(self) -> int:
        return len(self.entries)

    @property
    def selected_files(self) -> List[FileEntry]:
        return [e for e in self.entries if e.selected]

    @property
    def selected_bytes(self) -> int:
        return sum(e.size_bytes for e in self.selected_files)


# ── App state ─────────────────────────────────────────────────────────────────

class AppState:
    """
    Single instance — holds all runtime state.
    Access via the module-level `state` object below.
    """

    def __init__(self):
        # Navigation
        self.current_page: Page = Page.TEMP_FILES

        # Scan / clean state
        self.scan_status: ScanStatus = ScanStatus.IDLE
        self.scan_result: ScanResult = ScanResult()

        # Status bar message
        self.status_message: str = "Ready"

        # Progress (0.0 → 1.0)
        self.progress: float = 0.0

        # Stats — updated after each successful clean
        self.total_cleaned_bytes:  int = 0
        self.total_cleaned_files:  int = 0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def reset_scan(self):
        """Call this before starting a new scan."""
        self.scan_status = ScanStatus.IDLE
        self.scan_result = ScanResult()
        self.progress    = 0.0
        self.status_message = "Ready"

    def set_status(self, message: str):
        self.status_message = message

    def set_progress(self, value: float):
        """value: 0.0 to 1.0"""
        self.progress = max(0.0, min(1.0, value))

    def record_clean(self, files_cleaned: int, bytes_cleaned: int):
        self.total_cleaned_files += files_cleaned
        self.total_cleaned_bytes += bytes_cleaned


# ── Module-level singleton ─────────────────────────────────────────────────────
# Import this everywhere:   from app.state import state

state = AppState()