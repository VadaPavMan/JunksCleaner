"""
ui/components/file_table.py

FileTable — displays scan results in a scrollable table.
Uses ttk.Treeview (standard library) embedded inside a CTkFrame.

Columns: Checkbox | File Name | Size | Modified | Full Path
Supports: select all, deselect all, individual row toggle.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from app.state import ScanResult, FileEntry
from utils.file_utils import format_size
from utils.logger import get_logger
from typing import Callable, Optional

logger = get_logger(__name__)


class FileTable(ctk.CTkFrame):
    """
    Scrollable file results table.

    Args:
        master:        parent widget
        on_selection_change: called whenever checkbox state changes
                             — receives updated ScanResult
    """

    def __init__(
        self,
        master,
        on_selection_change: Optional[Callable[[ScanResult], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._result: Optional[ScanResult] = None
        self._on_selection_change = on_selection_change
        self._row_ids: list[str] = []   # treeview item IDs in order

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(0, weight=0)   # toolbar row
        self.grid_rowconfigure(1, weight=1)   # table row (expands)
        self.grid_columnconfigure(0, weight=1)

        # Toolbar — select all / deselect all / summary
        self._build_toolbar()

        # Table frame
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Style the treeview to match CTk dark theme
        self._apply_treeview_style()

        # Treeview
        self._tree = ttk.Treeview(
            table_frame,
            columns=("selected", "name", "size", "modified", "path"),
            show="headings",
            selectmode="browse",
            style="JunksCleaner.Treeview",
        )

        # Column headers + widths
        self._tree.heading("selected", text="✓",    anchor="center")
        self._tree.heading("name",     text="Name",     anchor="w")
        self._tree.heading("size",     text="Size",     anchor="e")
        self._tree.heading("modified", text="Modified", anchor="w")
        self._tree.heading("path",     text="Full Path",anchor="w")

        self._tree.column("selected", width=36,  minwidth=36,  stretch=False, anchor="center")
        self._tree.column("name",     width=200, minwidth=100, stretch=True,  anchor="w")
        self._tree.column("size",     width=80,  minwidth=60,  stretch=False, anchor="e")
        self._tree.column("modified", width=130, minwidth=100, stretch=False, anchor="w")
        self._tree.column("path",     width=300, minwidth=150, stretch=True,  anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",  command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Click to toggle selection
        self._tree.bind("<Button-1>", self._on_row_click)

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent", height=36)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        bar.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(
            bar, text="Select All", width=90, height=28,
            command=self._select_all,
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            bar, text="Deselect All", width=100, height=28,
            fg_color="transparent", border_width=1,
            command=self._deselect_all,
        ).grid(row=0, column=1, padx=(0, 12))

        self._summary_label = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self._summary_label.grid(row=0, column=3, sticky="e")

    def _apply_treeview_style(self):
        """Style the ttk.Treeview to roughly match CTk dark theme."""
        style = ttk.Style()
        style.theme_use("default")

        bg      = "#2b2b2b"
        fg      = "#dcddde"
        sel_bg  = "#3d5a80"
        header  = "#1f1f1f"

        style.configure(
            "JunksCleaner.Treeview",
            background=bg,
            foreground=fg,
            fieldbackground=bg,
            borderwidth=0,
            rowheight=24,
            font=("Segoe UI", 11),
        )
        style.configure(
            "JunksCleaner.Treeview.Heading",
            background=header,
            foreground="#aaaaaa",
            borderwidth=0,
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "JunksCleaner.Treeview",
            background=[("selected", sel_bg)],
            foreground=[("selected", "#ffffff")],
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def load_result(self, result: ScanResult):
        """Populate the table from a ScanResult."""
        self._result = result
        self._row_ids.clear()
        self._tree.delete(*self._tree.get_children())

        for entry in result.entries:
            name = entry.path.split("\\")[-1].split("/")[-1]
            check = "☑" if entry.selected else "☐"

            iid = self._tree.insert(
                "", "end",
                values=(
                    check,
                    name,
                    format_size(entry.size_bytes),
                    entry.modified,
                    entry.path,
                ),
                tags=("selected" if entry.selected else "deselected",),
            )
            self._row_ids.append(iid)

        self._tree.tag_configure("selected",   background="#2b2b2b")
        self._tree.tag_configure("deselected", background="#222222", foreground="#666666")

        self._update_summary()
        logger.debug(f"FileTable loaded {len(result.entries)} entries")

    def clear(self):
        self._result = None
        self._row_ids.clear()
        self._tree.delete(*self._tree.get_children())
        self._summary_label.configure(text="")

    # ── Selection ─────────────────────────────────────────────────────────────

    def _on_row_click(self, event):
        """Toggle selection on the clicked row."""
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self._tree.identify_row(event.y)
        if not row_id or self._result is None:
            return

        idx = self._row_ids.index(row_id) if row_id in self._row_ids else -1
        if idx < 0 or idx >= len(self._result.entries):
            return

        entry = self._result.entries[idx]
        entry.selected = not entry.selected

        check = "☑" if entry.selected else "☐"
        tag   = "selected" if entry.selected else "deselected"
        vals  = self._tree.item(row_id, "values")
        self._tree.item(row_id, values=(check, *vals[1:]), tags=(tag,))

        self._update_summary()

        if self._on_selection_change:
            self._on_selection_change(self._result)

    def _select_all(self):
        self._set_all(True)

    def _deselect_all(self):
        self._set_all(False)

    def _set_all(self, selected: bool):
        if self._result is None:
            return

        check = "☑" if selected else "☐"
        tag   = "selected" if selected else "deselected"

        for i, iid in enumerate(self._row_ids):
            if i < len(self._result.entries):
                self._result.entries[i].selected = selected
                vals = self._tree.item(iid, "values")
                self._tree.item(iid, values=(check, *vals[1:]), tags=(tag,))

        self._update_summary()
        if self._on_selection_change and self._result:
            self._on_selection_change(self._result)

    def _update_summary(self):
        if self._result is None:
            self._summary_label.configure(text="")
            return

        sel   = self._result.selected_files
        total = self._result.total_files
        size  = format_size(self._result.selected_bytes)
        self._summary_label.configure(
            text=f"{len(sel)} of {total} selected  ·  {size}"
        )