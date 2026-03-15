"""
ui/sidebar.py

Sidebar — left navigation panel.
Displays nav buttons for each cleaner and settings.
Calls on_navigate(Page) when a button is clicked.
"""

import customtkinter as ctk
from app.state import Page
from utils.logger import get_logger
from typing import Callable

logger = get_logger(__name__)


# Nav item definitions: (label, Page enum, icon character)
NAV_ITEMS = [
    ("Temp Files",     Page.TEMP_FILES,    "🗑"),
    ("Browser Cache",  Page.BROWSER_CACHE, "🌐"),
    ("Recycle Bin",    Page.RECYCLE_BIN,   "♻"),
    ("Startup Apps",   Page.STARTUP,       "⚡"),
]

BOTTOM_ITEMS = [
    ("Settings",       Page.SETTINGS,      "⚙"),
]


class Sidebar(ctk.CTkFrame):
    """
    Left navigation panel.

    Args:
        master:       parent widget
        on_navigate:  callback(Page) — called when user clicks a nav item
    """

    def __init__(self, master, on_navigate: Callable[[Page], None], **kwargs):
        super().__init__(master, width=180, corner_radius=8, **kwargs)
        self.on_navigate = on_navigate
        self._buttons: dict[Page, ctk.CTkButton] = {}
        self._active_page: Page | None = None

        self.grid_propagate(False)   # keep fixed width
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(1, weight=1)   # spacer row pushes bottom items down
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # App title / logo area
        title_label = ctk.CTkLabel(
            self,
            text="🧹 Junks Cleaner",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        title_label.grid(row=row, column=0, padx=16, pady=(18, 4), sticky="w")
        row += 1

        version_label = ctk.CTkLabel(
            self,
            text="v0.1.0 — alpha",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        version_label.grid(row=row, column=0, padx=16, pady=(0, 14), sticky="w")
        row += 1

        # Section label
        section_label = ctk.CTkLabel(
            self,
            text="CLEANERS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray",
        )
        section_label.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        row += 1

        # Main nav items
        for label, page, icon in NAV_ITEMS:
            btn = self._make_nav_button(label, page, icon)
            btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
            self._buttons[page] = btn
            row += 1

        # Spacer — pushes settings to bottom
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.grid(row=row, column=0, sticky="nsew")
        self.grid_rowconfigure(row, weight=1)
        row += 1

        # Divider
        divider = ctk.CTkFrame(self, height=1, fg_color="gray30")
        divider.grid(row=row, column=0, padx=10, pady=8, sticky="ew")
        row += 1

        # Bottom items (Settings)
        for label, page, icon in BOTTOM_ITEMS:
            btn = self._make_nav_button(label, page, icon)
            btn.grid(row=row, column=0, padx=10, pady=(2, 10), sticky="ew")
            self._buttons[page] = btn
            row += 1

        # Activate first item by default
        if NAV_ITEMS:
            self.set_active(NAV_ITEMS[0][1])

    def _make_nav_button(self, label: str, page: Page, icon: str) -> ctk.CTkButton:
        return ctk.CTkButton(
            self,
            text=f"  {icon}  {label}",
            anchor="w",
            height=36,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=13),
            command=lambda p=page: self._on_click(p),
        )

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_click(self, page: Page):
        self.set_active(page)
        self.on_navigate(page)
        logger.debug(f"Sidebar navigated to: {page.value}")

    def set_active(self, page: Page):
        """Highlight the active nav button, reset all others."""
        if self._active_page == page:
            return

        # Reset previous
        if self._active_page and self._active_page in self._buttons:
            self._buttons[self._active_page].configure(
                fg_color="transparent"
            )

        # Highlight new
        if page in self._buttons:
            self._buttons[page].configure(
                fg_color=("gray75", "gray30")
            )

        self._active_page = page