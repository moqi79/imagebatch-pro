"""自定义组件：拖放区域、日志面板。"""
import os
import tkinter as tk
from tkinter import ttk, filedialog


class DropArea(tk.Frame):
    """可点击选择或拖拽放入文件夹的区域。

    拖拽功能依赖可选库 tkinterdnd2；未安装时退化为点击选择。
    """

    def __init__(self, master, label="拖拽文件夹到此处，或点击选择", on_drop=None, **kw):
        super().__init__(master, **kw)
        self.on_drop = on_drop
        self.path_var = tk.StringVar()

        self.configure(relief="groove", bd=2, bg="#fafafa")
        self.columnconfigure(0, weight=1)

        self.label = tk.Label(
            self, text=label, padx=12, pady=18,
            bg="#fafafa", fg="#666666", justify="center",
        )
        self.label.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        self.path_entry = ttk.Entry(self, textvariable=self.path_var)
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        btn = ttk.Button(self, text="浏览...", command=self._browse)
        btn.grid(row=1, column=1, padx=(0, 12), pady=(0, 8))

        self._setup_dnd()
        self._bind_click()

    def _bind_click(self):
        self.label.bind("<Button-1>", lambda e: self._browse())
        self.bind("<Button-1>", lambda e: self._browse())

    def _browse(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get() or ".")
        if path:
            self.path_var.set(path)
            if self.on_drop:
                self.on_drop(path)

    def _setup_dnd(self):
        try:
            import tkinterdnd2  # noqa: F401
        except ImportError:
            return
        # 若上层使用了 TkinterDnD.Tk，此处才能注册
        try:
            self.drop_target_register("DND_Files")  # type: ignore[attr-defined]
            self.dnd_bind("<<Drop>>", self._on_drop_dnd)  # type: ignore[attr-defined]
            self.label.drop_target_register("DND_Files")  # type: ignore[attr-defined]
            self.label.dnd_bind("<<Drop>>", self._on_drop_dnd)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _on_drop_dnd(self, event):
        path = event.data.strip().strip("{}")
        if path and os.path.isdir(path):
            self.path_var.set(path)
            if self.on_drop:
                self.on_drop(path)

    def get(self):
        return self.path_var.get()


class LogPanel(ttk.Frame):
    """带滚动条的只读日志文本区。"""

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.text = tk.Text(
            self, height=8, wrap="word", state="disabled",
            bg="#1e1e1e", fg="#e0e0e0", insertbackground="#e0e0e0",
            font=("Consolas", 9),
        )
        scroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def append(self, message):
        self.text.configure(state="normal")
        self.text.insert("end", message + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
