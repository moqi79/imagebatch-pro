"""弹窗对话框。"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class AboutDialog(tk.Toplevel):
    """关于对话框。"""

    def __init__(self, master, version):
        super().__init__(master)
        self.title("关于 ImageBatch Pro")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        tk.Label(self, text="ImageBatch Pro", font=("", 16, "bold")).pack()
        tk.Label(self, text=f"版本 {version}").pack(pady=(0, 8))
        tk.Label(
            self,
            text="一键批量压缩、改尺寸、加水印、转格式\n纯本地运行，隐私零泄露",
            justify="center", fg="#666666",
        ).pack(pady=(0, 12))
        ttk.Button(self, text="确定", command=self.destroy).pack()
        self.transient(master)
        self.grab_set()


def show_error(master, title, message):
    messagebox.showerror(title, message, parent=master)


def show_info(master, title, message):
    messagebox.showinfo(title, message, parent=master)


def confirm(master, title, message):
    return messagebox.askyesno(title, message, parent=master)
