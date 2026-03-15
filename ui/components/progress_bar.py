"""
ui/components/progress_bar.py

ScanProgressBar — a labelled progress bar component.
Shows a CTk progress bar + a status label + file count below it.

Usage:
    bar = ScanProgressBar(parent)
    bar.pack(fill="x", padx=16)

    bar.start("Scanning...")          # show indeterminate spin
    bar.update(42, 200, "file.tmp")   # update to 42/200
    bar.finish("Done — 200 files")    # set to 100%, show message
    bar.reset()                       # hide and clear
"""

import customtkinter as ctk
from utils.logger import get_logger

logger = get_logger(__name__)


class ScanProgressBar(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._indeterminate = False
        self._build()
        self.reset()

    def _build(self):
        # Main label — "Scanning C:\\Windows\\Temp..."
        self._label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
        )
        self._label.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # Progress bar
        self._bar = ctk.CTkProgressBar(self, height=8)
        self._bar.set(0)
        self._bar.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # Sub-label — "42 / 200 files"
        self._sub_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        )
        self._sub_label.grid(row=2, column=0, sticky="w")

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, message: str = "Scanning..."):
        """Show indeterminate progress (spinning / animated)."""
        self._label.configure(text=message)
        self._sub_label.configure(text="")
        self._bar.configure(mode="indeterminate")
        self._bar.start()
        self._indeterminate = True
        self.grid()

    def update(self, current: int, total: int, current_file: str = ""):
        """Update to a specific progress value."""
        if self._indeterminate:
            self._bar.stop()
            self._bar.configure(mode="determinate")
            self._indeterminate = False

        fraction = current / total if total > 0 else 0
        self._bar.set(fraction)

        # Truncate long file paths for display
        display_file = current_file
        if len(display_file) > 60:
            display_file = "..." + display_file[-57:]

        self._label.configure(text=display_file)
        self._sub_label.configure(text=f"{current:,} / {total:,} files")
        self.grid()

    def finish(self, message: str = "Done"):
        """Set bar to 100% and show a completion message."""
        if self._indeterminate:
            self._bar.stop()
            self._bar.configure(mode="determinate")
            self._indeterminate = False
        self._bar.set(1.0)
        self._label.configure(text=message)
        self._sub_label.configure(text="")
        self.grid()

    def reset(self):
        """Clear and hide the progress bar."""
        if self._indeterminate:
            self._bar.stop()
            self._indeterminate = False
        self._bar.configure(mode="determinate")
        self._bar.set(0)
        self._label.configure(text="")
        self._sub_label.configure(text="")