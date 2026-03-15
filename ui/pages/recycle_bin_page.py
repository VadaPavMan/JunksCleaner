"""ui/pages/recycle_bin_page.py — Phase 3"""
import customtkinter as ctk

class RecycleBinPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="Recycle Bin Cleaner",
            font=ctk.CTkFont(size=22, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Coming in Phase 3.",
            text_color="gray").pack()
    def on_show(self): pass
