from tkinter import filedialog
import os


class FileHandler:
    def open_log_file(self):
        return filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
