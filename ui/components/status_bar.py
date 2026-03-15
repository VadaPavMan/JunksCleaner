"""ui/components/status_bar.py"""
import customtkinter as ctk
from utils.logger import get_logger
logger = get_logger(__name__)

class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=28, corner_radius=6, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self._label = ctk.CTkLabel(
            self, text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray", anchor="w",
        )
        self._label.grid(row=0, column=0, padx=12, sticky="w")

    def set_message(self, message: str):
        self._label.configure(text=message)
