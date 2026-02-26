import tkinter as tk
from tkinter import ttk
class SecureTable(ttk.Treeview):

    def __init__(self, parent):
        super().__init__(parent, columns=("ID", "Title", "Username"), show="headings")

        self.heading("ID", text="ID")
        self.heading("Title", text="Title")
        self.heading("Username", text="Username")

        self.column("ID", width=50)
        self.column("Title", width=200)
        self.column("Username", width=200)

        self.pack(fill="both", expand=True)

    def insert(self, entry_id, title, username):
        super().insert("", "end", values=(entry_id, title, username))

    def clear(self):
        for item in self.get_children():
            self.delete(item)

    def get_selected(self):
        selected = self.selection()
        if not selected:
            return None

        values = self.item(selected[0], "values")
        return int(values[0]), values[1], values[2]
