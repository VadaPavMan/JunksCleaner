"""ui/pages/settings_page.py — Phase 6"""
import customtkinter as ctk

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="Settings",
            font=ctk.CTkFont(size=22, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Coming in Phase 6.",
            text_color="gray").pack()
    def on_show(self): pass
