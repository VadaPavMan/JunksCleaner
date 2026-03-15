"""
ui/components/confirm_dialog.py

ConfirmDialog — a blocking modal dialog used before any destructive action.

Usage:
    result = ConfirmDialog.ask(
        parent=self,
        title="Delete Files",
        message="Delete 42 files (128 MB)?",
        detail="This cannot be undone.",
        confirm_text="Yes, Delete",
        cancel_text="Cancel",
        danger=True,    # makes confirm button red
    )
    if result:
        do_the_delete()
"""

import customtkinter as ctk
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfirmDialog(ctk.CTkToplevel):
    """
    Modal confirmation dialog.
    Blocks until the user clicks confirm or cancel.
    Returns True if confirmed, False otherwise.
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        detail: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str  = "Cancel",
        danger: bool = False,
    ):
        super().__init__(parent)

        self._result = False

        # Window setup
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)    # stays on top of parent
        self.grab_set()           # block interaction with parent

        self._build(message, detail, confirm_text, cancel_text, danger)

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width()  // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w, h = 380, 180 if not detail else 210
        self.geometry(f"{w}x{h}+{px - w//2}+{py - h//2}")

        # Handle window close (X button) as cancel
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self, message, detail, confirm_text, cancel_text, danger):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(padx=24, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        # Icon + message
        ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=320,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        if detail:
            ctk.CTkLabel(
                frame,
                text=detail,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=320,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        # Buttons
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="e")

        ctk.CTkButton(
            btn_row,
            text=cancel_text,
            width=100, height=32,
            fg_color="transparent",
            border_width=1,
            command=self._cancel,
        ).pack(side="left", padx=(0, 8))

        confirm_color = ("#c0392b", "#e74c3c") if danger else None
        ctk.CTkButton(
            btn_row,
            text=confirm_text,
            width=120, height=32,
            fg_color=confirm_color,
            command=self._confirm,
        ).pack(side="left")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _confirm(self):
        self._result = True
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self._result = False
        self.grab_release()
        self.destroy()

    # ── Class method — preferred way to use this ──────────────────────────────

    @classmethod
    def ask(
        cls,
        parent,
        title: str,
        message: str,
        detail: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str  = "Cancel",
        danger: bool = False,
    ) -> bool:
        """
        Show the dialog and block until dismissed.
        Returns True if the user clicked Confirm, False otherwise.
        """
        dialog = cls(
            parent=parent,
            title=title,
            message=message,
            detail=detail,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            danger=danger,
        )
        parent.wait_window(dialog)
        logger.debug(f"ConfirmDialog '{title}' result: {dialog._result}")
        return dialog._result