"""
ui/main_window.py

MainWindow — the root CTk window.
Owns the top-level layout:

  ┌─────────────────────────────────────────────────┐
  │  Sidebar (180px)  │  Content Area (fills rest)  │
  │                   │                             │
  │  [Temp Files]     │  <active page renders here> │
  │  [Browser Cache]  │                             │
  │  [Recycle Bin]    │                             │
  │  [Startup Apps]   │                             │
  │  ─────────────    │                             │
  │  [Settings]       │                             │
  ├───────────────────┴─────────────────────────────┤
  │  Status bar                                     │
  └─────────────────────────────────────────────────┘
"""

import customtkinter as ctk
from app.state import state, Page
from ui.sidebar import Sidebar
from ui.components.status_bar import StatusBar
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(ctk.CTk):
    """
    Root window. Builds the shell layout and wires up
    sidebar navigation to page switching.
    """

    def __init__(self):
        super().__init__()
        self._pages: dict = {}           # page_name → CTkFrame
        self._active_page = None

        self._build_layout()
        self._load_pages()
        self._show_page(state.current_page)

        logger.debug("MainWindow built")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Set up the three regions: sidebar, content, status bar."""

        # Root grid: 2 rows (content + status), 2 cols (sidebar + content)
        self.grid_rowconfigure(0, weight=1)      # content row expands
        self.grid_rowconfigure(1, weight=0)      # status bar fixed height
        self.grid_columnconfigure(0, weight=0)   # sidebar fixed width
        self.grid_columnconfigure(1, weight=1)   # content expands

        # Sidebar
        self.sidebar = Sidebar(
            master=self,
            on_navigate=self._show_page,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))

        # Content area — pages render inside here
        self.content_frame = ctk.CTkFrame(self, corner_radius=8)
        self.content_frame.grid(
            row=0, column=1,
            sticky="nsew",
            padx=10, pady=(10, 0),
        )
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Status bar — spans full width at bottom
        self.status_bar = StatusBar(master=self)
        self.status_bar.grid(
            row=1, column=0, columnspan=2,
            sticky="ew",
            padx=10, pady=(4, 8),
        )

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _load_pages(self):
        """
        Instantiate all page frames and stack them in the content area.
        Only the active page is visible at any time.
        """
        from ui.pages.temp_cleaner_page  import TempCleanerPage
        from ui.pages.browser_cleaner_page import BrowserCleanerPage
        from ui.pages.recycle_bin_page   import RecycleBinPage
        from ui.pages.settings_page      import SettingsPage

        page_map = {
            Page.TEMP_FILES:    TempCleanerPage,
            Page.BROWSER_CACHE: BrowserCleanerPage,
            Page.RECYCLE_BIN:   RecycleBinPage,
            Page.SETTINGS:      SettingsPage,
        }

        for page_enum, PageClass in page_map.items():
            frame = PageClass(master=self.content_frame)
            frame.grid(row=0, column=0, sticky="nsew")
            self._pages[page_enum] = frame

        logger.debug(f"Loaded {len(self._pages)} pages")

    def _show_page(self, page: Page):
        """Raise the selected page frame to the front."""
        if page not in self._pages:
            logger.warning(f"Page not found: {page}")
            return

        # Hide current
        if self._active_page:
            self._pages[self._active_page].grid_remove()

        # Show new
        self._pages[page].grid()
        self._active_page = page
        state.current_page = page

        # Tell the page it's now visible (optional hook)
        page_frame = self._pages[page]
        if hasattr(page_frame, "on_show"):
            page_frame.on_show()

        logger.debug(f"Navigated to: {page.value}")

    # ── Status bar refresh ────────────────────────────────────────────────────

    def refresh_status(self):
        """Pull latest status message from state and update the status bar."""
        self.status_bar.set_message(state.status_message)
        self.after(500, self.refresh_status)   # poll every 500ms