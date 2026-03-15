"""
app/app.py

JunksCleanerApp — sets up the CustomTkinter root window and
hands off to the main window layout.
"""

import customtkinter as ctk
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class JunksCleanerApp:
    """
    Top-level application class.
    Responsible for:
      - Configuring CTk appearance (theme, color mode)
      - Creating the root Tk window
      - Launching the main window UI
      - Starting the event loop
    """

    def __init__(self):
        logger.info("Initializing JunksCleanerApp")
        self._configure_ctk()
        self._root = self._build_root()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _configure_ctk(self):
        """Apply global CTk appearance settings."""
        ctk.set_appearance_mode(settings.get("appearance_mode", "dark"))
        ctk.set_default_color_theme(settings.get("color_theme", "blue"))
        logger.debug("CTk appearance configured")

    def _build_root(self) -> ctk.CTk:
        """Create and configure the root window."""
        from ui.main_window import MainWindow

        root = MainWindow()

        # Window properties
        root.title("Junks Cleaner")
        root.geometry(
            f"{settings.get('window_width', 960)}"
            f"x{settings.get('window_height', 620)}"
        )
        root.minsize(800, 520)

        # Center on screen
        root.update_idletasks()
        self._center_window(root)

        # Handle window close button
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        logger.info("Root window created")
        return root

    def _center_window(self, window: ctk.CTk):
        """Position the window in the center of the screen."""
        w = window.winfo_width()
        h = window.winfo_height()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        window.geometry(f"{w}x{h}+{x}+{y}")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def run(self):
        """Start the CTk main event loop. Blocks until window is closed."""
        logger.info("Entering main event loop")
        self._root.mainloop()

    def _on_close(self):
        """Called when the user clicks the window's X button."""
        logger.info("Close requested by user")
        # Cancel any running background workers before exit
        try:
            from app.state import state
            state.set_status("Closing...")
        except Exception:
            pass
        self._root.destroy()