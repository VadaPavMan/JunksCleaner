"""ui/pages/browser_cleaner_page.py — Phase 2"""
import customtkinter as ctk

class BrowserCleanerPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="Browser Cache Cleaner",
            font=ctk.CTkFont(size=22, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Coming in Phase 2.",
            text_color="gray").pack()
    def on_show(self): pass
