"""社区版主窗口（tkinter）。"""
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import config
from core.processor import ProcessingConfig
from core.batch import BatchProcessor
from main import load_presets
from .widgets import DropArea, LogPanel
from .dialogs import AboutDialog, show_error


class CommunityApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"ImageBatch Pro v{config.__version__}")
        self.root.geometry("720x680")
        self.root.minsize(680, 640)
        self._center_window(720, 680)

        self.processor = None
        self._worker = None
        self._queue: queue.Queue = queue.Queue()
        self._processing = False

        self._build_menu()
        self._build_ui()
        self._load_presets()
        self._poll_queue()

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3
        self.root.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        m = tk.Menu(menubar, tearoff=0)
        m.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=m)
        h = tk.Menu(menubar, tearoff=0)
        h.add_command(label="关于", command=lambda: AboutDialog(self.root, config.__version__))
        menubar.add_cascade(label="帮助", menu=h)
        self.root.configure(menu=menubar)

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}
        f = ttk.Frame(self.root, padding=10)
        f.pack(fill="both", expand=True)
        f.columnconfigure(0, weight=1)

        # ---- 目录区 ----
        dir_frame = ttk.LabelFrame(f, text="目录", padding=10)
        dir_frame.grid(row=0, column=0, sticky="ew", **pad)
        dir_frame.columnconfigure(0, weight=1)

        ttk.Label(dir_frame, text="输入目录").grid(row=0, column=0, sticky="w")
        self.drop_input = DropArea(dir_frame, "拖拽文件夹到此处，或点击选择",
                                   on_drop=self._on_input_drop)
        self.drop_input.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(dir_frame, text="输出目录").grid(row=2, column=0, sticky="w")
        out_row = ttk.Frame(dir_frame)
        out_row.grid(row=3, column=0, sticky="ew")
        out_row.columnconfigure(0, weight=1)
        self.var_output = tk.StringVar()
        ttk.Entry(out_row, textvariable=self.var_output).grid(row=0, column=0, sticky="ew")
        ttk.Button(out_row, text="浏览...", command=self._browse_output).grid(
            row=0, column=1, padx=(6, 0))

        # ---- 处理选项区 ----
        opt_frame = ttk.LabelFrame(f, text="处理选项", padding=10)
        opt_frame.grid(row=1, column=0, sticky="ew", **pad)
        opt_frame.columnconfigure(1, weight=1)

        # 压缩
        self.var_compress = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="压缩", variable=self.var_compress,
                        command=self._toggle_states).grid(row=0, column=0, sticky="w")
        ttk.Label(opt_frame, text="目标大小(KB):").grid(row=0, column=1, sticky="w", padx=(20, 0))
        self.var_target_kb = tk.IntVar(value=500)
        ttk.Entry(opt_frame, textvariable=self.var_target_kb, width=8).grid(row=0, column=2, sticky="w")
        ttk.Label(opt_frame, text="最低质量:").grid(row=0, column=3, sticky="w", padx=(20, 0))
        self.var_min_q = tk.IntVar(value=40)
        ttk.Entry(opt_frame, textvariable=self.var_min_q, width=6).grid(row=0, column=4, sticky="w")

        # 尺寸
        self.var_resize = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="改尺寸", variable=self.var_resize,
                        command=self._toggle_states).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(opt_frame, text="宽:").grid(row=1, column=1, sticky="w", padx=(20, 0))
        self.var_w = tk.IntVar(value=1080)
        ttk.Entry(opt_frame, textvariable=self.var_w, width=6).grid(row=1, column=2, sticky="w")
        ttk.Label(opt_frame, text="高:").grid(row=1, column=3, sticky="w", padx=(20, 0))
        self.var_h = tk.IntVar(value=1440)
        ttk.Entry(opt_frame, textvariable=self.var_h, width=6).grid(row=1, column=4, sticky="w")
        ttk.Label(opt_frame, text="模式:").grid(row=2, column=1, sticky="w", padx=(20, 0))
        self.var_mode = tk.StringVar(value="cover")
        ttk.Combobox(opt_frame, textvariable=self.var_mode, width=10, state="readonly",
                     values=["cover", "contain", "stretch", "pad"]).grid(
            row=2, column=2, sticky="w", pady=2)

        # 格式转换
        self.var_convert = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="格式转换", variable=self.var_convert,
                        command=self._toggle_states).grid(row=3, column=0, sticky="w")
        ttk.Label(opt_frame, text="目标格式:").grid(row=3, column=1, sticky="w", padx=(20, 0))
        self.var_format = tk.StringVar(value="jpg")
        ttk.Combobox(opt_frame, textvariable=self.var_format, width=8, state="readonly",
                     values=config.WRITE_FORMATS).grid(row=3, column=2, sticky="w")

        # 水印
        self.var_wm = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="水印", variable=self.var_wm,
                        command=self._toggle_states).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(opt_frame, text="文字:").grid(row=4, column=1, sticky="w", padx=(20, 0))
        self.var_wm_text = tk.StringVar(value="@MyBrand")
        ttk.Entry(opt_frame, textvariable=self.var_wm_text, width=14).grid(
            row=4, column=2, columnspan=2, sticky="w")
        ttk.Label(opt_frame, text="位置:").grid(row=4, column=4, sticky="w")
        self.var_wm_pos = tk.StringVar(value="bottom-right")
        ttk.Combobox(opt_frame, textvariable=self.var_wm_pos, width=14, state="readonly",
                     values=["top-left", "top-center", "top-right", "center",
                             "bottom-left", "bottom-center", "bottom-right",
                             "tile", "random"]).grid(row=5, column=2, sticky="w")

        # ---- 预设区 ----
        pre_frame = ttk.LabelFrame(f, text="预设模板", padding=10)
        pre_frame.grid(row=2, column=0, sticky="ew", **pad)
        pre_frame.columnconfigure(0, weight=1)
        self.var_preset = tk.StringVar()
        self.cmb_preset = ttk.Combobox(pre_frame, textvariable=self.var_preset,
                                      state="readonly")
        self.cmb_preset.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(pre_frame, text="应用预设", command=self._apply_preset).grid(
            row=0, column=1)
        ttk.Button(pre_frame, text="刷新列表", command=self._load_presets).grid(
            row=0, column=2, padx=(6, 0))

        # ---- 控制区 ----
        ctrl_frame = ttk.Frame(f)
        ctrl_frame.grid(row=3, column=0, sticky="ew", **pad)
        self.btn_start = ttk.Button(ctrl_frame, text="▶ 开始处理", command=self._start)
        self.btn_start.grid(row=0, column=0)
        self.btn_pause = ttk.Button(ctrl_frame, text="⏸ 暂停", command=self._pause,
                                   state="disabled")
        self.btn_pause.grid(row=0, column=1, padx=6)
        ttk.Button(ctrl_frame, text="⏹ 取消", command=self._cancel).grid(row=0, column=2)
        ttk.Button(ctrl_frame, text="清空日志", command=self._clear_log).grid(
            row=0, column=3, padx=(6, 0))

        # ---- 进度与日志 ----
        self.var_progress = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(f, variable=self.var_progress,
                                        maximum=100)
        self.progress.grid(row=4, column=0, sticky="ew", **pad)
        self.lbl_status = ttk.Label(f, text="就绪", anchor="w")
        self.lbl_status.grid(row=5, column=0, sticky="w", padx=10)

        self.log = LogPanel(f)
        self.log.grid(row=6, column=0, sticky="nsew", **pad)
        f.rowconfigure(6, weight=1)

        self._toggle_states()

    # ---- 预设 ----
    def _load_presets(self):
        self.presets = load_presets()
        names = [f"{pid} — {data.get('name', '')}" for pid, data in self.presets.items()]
        self.cmb_preset["values"] = names
        if names:
            self.cmb_preset.current(0)

    def _apply_preset(self):
        sel = self.var_preset.get()
        if not sel:
            return
        pid = sel.split(" — ")[0]
        data = self.presets.get(pid)
        if not data:
            return
        params = data.get("params", {})
        if params.get("compress"):
            self.var_compress.set(True)
            self.var_target_kb.set(params["compress"].get("target_size_kb", 500))
            self.var_min_q.set(params["compress"].get("min_quality", 40))
        if params.get("resize"):
            self.var_resize.set(True)
            self.var_w.set(params["resize"].get("width", 1080))
            self.var_h.set(params["resize"].get("height", 1440))
            self.var_mode.set(params["resize"].get("mode", "cover"))
        if params.get("watermark"):
            self.var_wm.set(True)
            self.var_wm_text.set(params["watermark"].get("text", ""))
            self.var_wm_pos.set(params["watermark"].get("position", "bottom-right"))
        if params.get("format"):
            self.var_convert.set(True)
            self.var_format.set(params["format"])
        self._toggle_states()
        self.log.append(f"已应用预设: {data.get('name', pid)}")

    # ---- 目录 ----
    def _on_input_drop(self, path):
        if not self.var_output.get():
            self.var_output.set(os.path.join(path, "output"))

    def _browse_output(self):
        p = filedialog.askdirectory()
        if p:
            self.var_output.set(p)

    def _toggle_states(self):
        pass  # 输入框始终可编辑；按需可在此禁用未勾选的控件

    # ---- 处理 ----
    def _build_config(self):
        cfg = ProcessingConfig()
        if self.var_compress.get():
            cfg.compress = {"target_size_kb": self.var_target_kb.get(),
                             "min_quality": self.var_min_q.get()}
        if self.var_resize.get():
            cfg.resize = {"width": self.var_w.get(), "height": self.var_h.get(),
                          "mode": self.var_mode.get(), "background": "#FFFFFF",
                          "gravity": "center"}
        if self.var_convert.get():
            cfg.convert = {"format": self.var_format.get(), "quality": 85,
                           "keep_alpha": True}
            cfg.output_format = self.var_format.get()
        if self.var_wm.get() and self.var_wm_text.get():
            cfg.watermark_text = {
                "text": self.var_wm_text.get(),
                "position": self.var_wm_pos.get(),
                "font_size": 36, "color": "#FFFFFF", "opacity": 0.7,
            }
        return cfg

    def _start(self):
        input_dir = self.drop_input.get()
        output_dir = self.var_output.get()
        if not input_dir or not os.path.isdir(input_dir):
            show_error(self.root, "错误", "请选择有效的输入目录")
            return
        if not output_dir:
            output_dir = os.path.join(input_dir, "output")
            self.var_output.set(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        cfg = self._build_config()
        self._processing = True
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸ 暂停")
        self.processor = BatchProcessor(max_workers=config.MAX_WORKERS)
        self.log.clear()
        self.log.append(f"开始处理: {input_dir} -> {output_dir}")

        self._worker = threading.Thread(
            target=self._run_batch, args=(input_dir, output_dir, cfg), daemon=True)
        self._worker.start()

    def _run_batch(self, input_dir, output_dir, cfg):
        try:
            self.processor.process(
                input_dir, output_dir, cfg,
                progress_callback=lambda d, t: self._queue.put(("progress", d, t)),
                log_callback=lambda m: self._queue.put(("log", m)),
            )
        except Exception as e:  # noqa: BLE001
            self._queue.put(("error", str(e)))
        finally:
            self._queue.put(("done",))

    def _pause(self):
        if not self.processor:
            return
        if self.btn_pause.cget("text").startswith("⏸"):
            self.processor.pause()
            self.btn_pause.configure(text="▶ 继续")
            self.lbl_status.configure(text="已暂停")
        else:
            self.processor.resume()
            self.btn_pause.configure(text="⏸ 暂停")
            self.lbl_status.configure(text="处理中...")

    def _cancel(self):
        if self.processor and self._processing:
            self.processor.cancel()
            self.lbl_status.configure(text="正在取消...")

    def _poll_queue(self):
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg[0] == "progress":
                    _, done, total = msg
                    pct = (done / total * 100) if total else 0
                    self.var_progress.set(pct)
                    self.lbl_status.configure(
                        text=f"处理中: {done}/{total} ({pct:.0f}%)")
                elif msg[0] == "log":
                    self.log.append(msg[1])
                elif msg[0] == "error":
                    self.log.append(f"[错误] {msg[1]}")
                elif msg[0] == "done":
                    self._finish()
        except queue.Empty:
            pass
        self.root.after(120, self._poll_queue)

    def _finish(self):
        self._processing = False
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="⏸ 暂停")
        self.var_progress.set(100)
        self.lbl_status.configure(text="处理完成")
        self.log.append("处理完成。")

    def _clear_log(self):
        self.log.clear()
        self.var_progress.set(0)
        self.lbl_status.configure(text="就绪")

    def run(self):
        self.root.mainloop()
