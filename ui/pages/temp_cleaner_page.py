"""
ui/pages/temp_cleaner_page.py — Phase 1 complete UI
"""

import customtkinter as ctk
from app.state import state, ScanStatus, ScanResult
from ui.components.file_table import FileTable
from ui.components.progress_bar import ScanProgressBar
from ui.components.confirm_dialog import ConfirmDialog
from utils.thread_worker import run_in_background
from utils.file_utils import format_size
from utils.logger import get_logger

logger = get_logger(__name__)


class TempCleanerPage(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._scan_result = None
        self._active_worker = None
        self._path_vars = {}
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        row = 0

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=row, column=0, sticky="ew", padx=20, pady=(20, 0))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Temp File Cleaner",
            font=ctk.CTkFont(size=22, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header,
            text="Removes temporary files left behind by Windows and applications. Safe to clean at any time.",
            font=ctk.CTkFont(size=13), text_color="gray", anchor="w",
            wraplength=680, justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        row += 1

        # Divider
        ctk.CTkFrame(self, height=1, fg_color="gray25").grid(
            row=row, column=0, sticky="ew", padx=20, pady=14)
        row += 1

        # Paths section
        paths_frame = ctk.CTkFrame(self, fg_color="transparent")
        paths_frame.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 8))
        ctk.CTkLabel(paths_frame, text="Scan locations:",
            font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 8))
        self._paths_container = ctk.CTkFrame(paths_frame, fg_color="transparent")
        self._paths_container.pack(anchor="w", fill="x")
        row += 1

        # Action bar
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.grid(row=row, column=0, sticky="ew", padx=20, pady=(8, 4))
        action_bar.grid_columnconfigure(3, weight=1)

        self._scan_btn = ctk.CTkButton(action_bar, text="  Scan",
            width=110, height=36, command=self._start_scan)
        self._scan_btn.grid(row=0, column=0, padx=(0, 8))

        self._cancel_btn = ctk.CTkButton(action_bar, text="Cancel",
            width=90, height=36, fg_color="transparent", border_width=1,
            state="disabled", command=self._cancel)
        self._cancel_btn.grid(row=0, column=1, padx=(0, 16))

        self._clean_btn = ctk.CTkButton(action_bar, text="  Clean Selected",
            width=150, height=36,
            fg_color=("#c0392b", "#e74c3c"), hover_color=("#922b21", "#cb4335"),
            state="disabled", command=self._start_clean)
        self._clean_btn.grid(row=0, column=2)

        self._selected_label = ctk.CTkLabel(action_bar, text="",
            font=ctk.CTkFont(size=12), text_color="gray")
        self._selected_label.grid(row=0, column=3, sticky="e")
        row += 1

        # Progress bar
        self._progress = ScanProgressBar(self)
        self._progress.grid(row=row, column=0, sticky="ew", padx=20, pady=(4, 8))
        row += 1

        # File table — this row expands
        self.grid_rowconfigure(row, weight=1)
        self._table = FileTable(self, on_selection_change=self._on_selection_change)
        self._table.grid(row=row, column=0, sticky="nsew", padx=20, pady=(0, 8))
        row += 1

        # Summary bar
        self._summary_bar = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self._summary_bar.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 16))
        self._summary_bar.grid_columnconfigure(0, weight=1)
        self._summary_label = ctk.CTkLabel(self._summary_bar, text="",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
        self._summary_label.grid(row=0, column=0, sticky="w")
        self._session_label = ctk.CTkLabel(self._summary_bar, text="",
            font=ctk.CTkFont(size=12), text_color=("gray40", "gray60"), anchor="e")
        self._session_label.grid(row=0, column=1, sticky="e")

    def on_show(self):
        self._load_path_checkboxes()
        self._update_session_stats()

    def _load_path_checkboxes(self):
        for w in self._paths_container.winfo_children():
            w.destroy()
        self._path_vars.clear()
        try:
            from os_platform.detector import is_windows
            if is_windows():
                from os_platform.windows.paths import get_temp_paths
            else:
                from os_platform.linux.paths import get_temp_paths
            paths = get_temp_paths()
        except Exception as e:
            logger.error(f"Failed to load paths: {e}")
            paths = []

        if not paths:
            ctk.CTkLabel(self._paths_container,
                text="No temp paths found.", text_color="gray").pack(anchor="w")
            return

        cols = ctk.CTkFrame(self._paths_container, fg_color="transparent")
        cols.pack(fill="x")
        col_left  = ctk.CTkFrame(cols, fg_color="transparent")
        col_right = ctk.CTkFrame(cols, fg_color="transparent")
        col_left.pack(side="left", fill="x", expand=True)
        col_right.pack(side="left", fill="x", expand=True)

        for i, path in enumerate(paths):
            var = ctk.BooleanVar(value=True)
            self._path_vars[path] = var
            col = col_left if i % 2 == 0 else col_right
            ctk.CTkCheckBox(col, text=path, variable=var,
                font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)

    # Scan
    def _start_scan(self):
        selected_paths = [p for p, v in self._path_vars.items() if v.get()]
        if not selected_paths:
            self._set_summary("No paths selected.")
            return
        self._set_scanning_state(True)
        self._table.clear()
        self._scan_result = None
        self._progress.start("Preparing scan...")
        state.set_status("Scanning temp files...")

        from core.temp_cleaner import TempCleaner
        cleaner = TempCleaner()

        def do_scan(cancel_event=None):
            original_prop = TempCleaner.scan_paths.fget
            TempCleaner.scan_paths = property(lambda s: selected_paths)
            result = cleaner.scan(cancel_event=cancel_event,
                on_progress=lambda c, p: self.after(0, lambda c=c, p=p: self._progress.update(c, c, p)))
            TempCleaner.scan_paths = property(original_prop)
            return result

        self._active_worker = run_in_background(
            task=do_scan,
            on_result=self._on_scan_complete,
            on_error=self._on_error,
            on_done=lambda: self._set_scanning_state(False),
            ui_widget=self,
        )

    def _on_scan_complete(self, result):
        self._scan_result = result
        state.scan_result = result
        state.scan_status = ScanStatus.DONE
        if result.total_files == 0:
            self._progress.finish("Scan complete — no files found")
            self._set_summary("No temporary files found. Your system is clean!")
            state.set_status("Scan complete — nothing to clean")
            return
        self._table.load_result(result)
        self._progress.finish(f"Scan complete — {result.total_files:,} files found")
        self._clean_btn.configure(state="normal")
        self._update_selected_label(result)
        self._set_summary(f"Found {result.total_files:,} files  ·  {format_size(result.total_bytes)} total")
        state.set_status(f"Scan done — {result.total_files:,} files, {format_size(result.total_bytes)}")

    # Clean
    def _start_clean(self):
        if not self._scan_result:
            return
        selected = self._scan_result.selected_files
        if not selected:
            self._set_summary("No files selected.")
            return
        confirmed = ConfirmDialog.ask(
            parent=self.winfo_toplevel(),
            title="Confirm Clean",
            message=f"Delete {len(selected):,} files ({format_size(self._scan_result.selected_bytes)})?",
            detail="Deleted files cannot be recovered. Continue?",
            confirm_text="Yes, Delete",
            cancel_text="Cancel",
            danger=True,
        )
        if not confirmed:
            return
        self._set_cleaning_state(True)
        self._progress.start("Deleting files...")
        state.set_status("Cleaning temp files...")

        from core.temp_cleaner import TempCleaner
        cleaner = TempCleaner()
        scan_result = self._scan_result

        def do_clean(cancel_event=None):
            return cleaner.clean(scan_result=scan_result, cancel_event=cancel_event,
                on_progress=lambda c, t: self.after(0, lambda c=c, t=t: self._progress.update(c, t)))

        self._active_worker = run_in_background(
            task=do_clean,
            on_result=self._on_clean_complete,
            on_error=self._on_error,
            on_done=lambda: self._set_cleaning_state(False),
            ui_widget=self,
        )

    def _on_clean_complete(self, result):
        state.record_clean(result.files_deleted, result.bytes_freed)
        freed_str = format_size(result.bytes_freed)
        self._progress.finish(f"Done — {result.files_deleted:,} files deleted, {freed_str} freed")
        parts = [f"Deleted {result.files_deleted:,} files", f"{freed_str} freed"]
        if result.files_skipped > 0:
            parts.append(f"{result.files_skipped} skipped (in use)")
        self._set_summary("  ·  ".join(parts))
        self._update_session_stats()
        state.set_status(f"Clean complete — {freed_str} freed")
        if self._scan_result:
            error_paths = {e.split(":")[0] for e in result.errors}
            remaining = [e for e in self._scan_result.entries
                if not e.selected or e.path in error_paths]
            self._scan_result.entries = remaining
            self._scan_result.total_bytes = sum(e.size_bytes for e in remaining)
            if remaining:
                self._table.load_result(self._scan_result)
            else:
                self._table.clear()
                self._clean_btn.configure(state="disabled")

    def _cancel(self):
        if self._active_worker:
            self._active_worker.cancel()
        self._progress.reset()
        state.set_status("Cancelled")

    def _set_scanning_state(self, scanning):
        self._scan_btn.configure(state="disabled" if scanning else "normal")
        self._clean_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal" if scanning else "disabled")
        state.scan_status = ScanStatus.SCANNING if scanning else ScanStatus.DONE

    def _set_cleaning_state(self, cleaning):
        s = "disabled" if cleaning else "normal"
        self._scan_btn.configure(state=s)
        self._clean_btn.configure(state=s)
        self._cancel_btn.configure(state="normal" if cleaning else "disabled")

    def _on_selection_change(self, result):
        self._update_selected_label(result)

    def _update_selected_label(self, result):
        sel = result.selected_files
        self._selected_label.configure(
            text=f"{len(sel):,} selected  ·  {format_size(result.selected_bytes)}")
        self._clean_btn.configure(state="normal" if sel else "disabled")

    def _set_summary(self, text):
        self._summary_label.configure(text=text)

    def _update_session_stats(self):
        if state.total_cleaned_files > 0:
            self._session_label.configure(
                text=f"Session total: {state.total_cleaned_files:,} files  ·  {format_size(state.total_cleaned_bytes)} freed")

    def _on_error(self, error):
        logger.error(f"Operation failed: {error}", exc_info=True)
        self._progress.finish(f"Error: {error}")
        self._set_summary(f"An error occurred: {error}")
        state.set_status(f"Error: {error}")