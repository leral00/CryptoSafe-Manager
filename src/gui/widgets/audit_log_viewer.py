import tkinter as tk
from tkinter import ttk

class AuditLogViewer(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.label = ttk.Label(self, text="Audit Log Viewer (Stub for Sprint 5)")
        self.label.pack(pady=20)
