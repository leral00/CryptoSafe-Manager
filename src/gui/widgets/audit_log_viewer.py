import tkinter as tk
class AuditLogViewer(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Audit Log")

        tk.Label(self, text="Audit Log Viewer (Заглушка Sprint 1)").pack(padx=20, pady=20)
