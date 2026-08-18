"""专业版主窗口（PyQt5）。

专业版在社区版功能基础上增加：暗色主题、实时预览面板、预设管理器。
需安装 PyQt5：``pip install PyQt5``。
"""
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QFormLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox,
        QProgressBar, QTextEdit, QFileDialog, QSpinBox, QGroupBox, QStatusBar,
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QPixmap, QImage
    _HAS_QT = True
except ImportError as _e:  # pragma: no cover
    _HAS_QT = False
    raise ImportError("PyQt5 未安装，无法启动专业版界面") from _e

import os
import config
from core.processor import ProcessingConfig
from core.batch import BatchProcessor
from main import load_presets


class Worker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished_signal = pyqtSignal(list)

    def __init__(self, input_dir, output_dir, cfg):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.cfg = cfg
        self.processor = BatchProcessor(max_workers=config.MAX_WORKERS)

    def run(self):
        results = self.processor.process(
            self.input_dir, self.output_dir, self.cfg,
            progress_callback=lambda d, t: self.progress.emit(d, t),
            log_callback=lambda m: self.log.emit(m),
        )
        self.finished_signal.emit(results)

    def cancel(self):
        self.processor.cancel()


class ProMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ImageBatch Pro v{config.__version__} — 专业版")
        self.resize(820, 720)
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # 目录
        g_dir = QGroupBox("目录")
        dl = QFormLayout(g_dir)
        self.in_edit = QLineEdit()
        self.in_edit.setPlaceholderText("输入目录...")
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("输出目录...")
        dl.addRow("输入:", self._with_btn(self.in_edit, self._pick_in))
        dl.addRow("输出:", self._with_btn(self.out_edit, self._pick_out))
        root.addWidget(g_dir)

        # 选项
        g_opt = QGroupBox("处理选项")
        ol = QFormLayout(g_opt)
        self.cb_compress = QCheckBox("压缩")
        self.sp_target = QSpinBox(); self.sp_target.setRange(1, 100000); self.sp_target.setValue(500)
        self.cb_resize = QCheckBox("改尺寸")
        self.sp_w = QSpinBox(); self.sp_w.setRange(1, 99999); self.sp_w.setValue(1080)
        self.sp_h = QSpinBox(); self.sp_h.setRange(1, 99999); self.sp_h.setValue(1440)
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(["cover", "contain", "stretch", "pad"])
        self.cb_convert = QCheckBox("格式转换")
        self.cmb_format = QComboBox(); self.cmb_format.addItems(config.WRITE_FORMATS)
        self.cb_wm = QCheckBox("水印")
        self.ed_wm = QLineEdit("@MyBrand")
        self.cmb_wm_pos = QComboBox()
        self.cmb_wm_pos.addItems(
            ["top-left", "top-center", "top-right", "center",
             "bottom-left", "bottom-center", "bottom-right", "tile", "random"])

        ol.addRow(self.cb_compress, self._row(QLabel("目标KB:"), self.sp_target))
        ol.addRow(self.cb_resize, self._row(QLabel("宽:"), self.sp_w, QLabel("高:"), self.sp_h,
                                              QLabel("模式:"), self.cmb_mode))
        ol.addRow(self.cb_convert, self._row(QLabel("格式:"), self.cmb_format))
        ol.addRow(self.cb_wm, self._row(QLabel("文字:"), self.ed_wm, QLabel("位置:"), self.cmb_wm_pos))
        root.addWidget(g_opt)

        # 预设
        g_pre = QGroupBox("预设模板")
        pl = QHBoxLayout(g_pre)
        self.cmb_preset = QComboBox()
        pl.addWidget(self.cmb_preset)
        pl.addWidget(QPushButton("应用", clicked=self._apply_preset))
        root.addWidget(g_pre)

        # 控制
        ctl = QHBoxLayout()
        self.btn_start = QPushButton("▶ 开始处理", clicked=self._start)
        self.btn_cancel = QPushButton("⏹ 取消", clicked=self._cancel)
        ctl.addWidget(self.btn_start); ctl.addWidget(self.btn_cancel)
        root.addLayout(ctl)

        # 进度
        self.pb = QProgressBar()
        root.addWidget(self.pb)

        # 日志
        self.log = QTextEdit(readOnly=True)
        self.log.setStyleSheet("background:#1e1e1e; color:#e0e0e0; font-family:Consolas;")
        root.addWidget(self.log)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("就绪")

        self._load_presets()

    def _with_btn(self, edit, cmd):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit); b = QPushButton("浏览..."); b.clicked.connect(cmd); h.addWidget(b)
        return w

    def _row(self, *widgets):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0)
        for x in widgets:
            h.addWidget(x)
        return w

    def _pick_in(self):
        p = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if p:
            self.in_edit.setText(p)

    def _pick_out(self):
        p = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if p:
            self.out_edit.setText(p)

    def _load_presets(self):
        self.presets = load_presets()
        self.cmb_preset.clear()
        for pid, data in self.presets.items():
            self.cmb_preset.addItem(f"{pid} — {data.get('name', '')}", pid)

    def _apply_preset(self):
        pid = self.cmb_preset.currentData()
        data = self.presets.get(pid)
        if not data:
            return
        params = data.get("params", {})
        if params.get("compress"):
            self.cb_compress.setChecked(True)
            self.sp_target.setValue(params["compress"].get("target_size_kb", 500))
        if params.get("resize"):
            self.cb_resize.setChecked(True)
            self.sp_w.setValue(params["resize"].get("width", 1080))
            self.sp_h.setValue(params["resize"].get("height", 1440))
            self.cmb_mode.setCurrentText(params["resize"].get("mode", "cover"))
        if params.get("watermark"):
            self.cb_wm.setChecked(True)
            self.ed_wm.setText(params["watermark"].get("text", ""))
            self.cmb_wm_pos.setCurrentText(params["watermark"].get("position", "bottom-right"))
        if params.get("format"):
            self.cb_convert.setChecked(True)
            self.cmb_format.setCurrentText(params["format"])

    def _build_config(self):
        cfg = ProcessingConfig()
        if self.cb_compress.isChecked():
            cfg.compress = {"target_size_kb": self.sp_target.value(), "min_quality": 40}
        if self.cb_resize.isChecked():
            cfg.resize = {"width": self.sp_w.value(), "height": self.sp_h.value(),
                          "mode": self.cmb_mode.currentText(), "background": "#FFFFFF",
                          "gravity": "center"}
        if self.cb_convert.isChecked():
            cfg.convert = {"format": self.cmb_format.currentText(), "quality": 85}
            cfg.output_format = self.cmb_format.currentText()
        if self.cb_wm.isChecked() and self.ed_wm.text():
            cfg.watermark_text = {"text": self.ed_wm.text(),
                                  "position": self.cmb_wm_pos.currentText(),
                                  "font_size": 36, "color": "#FFFFFF", "opacity": 0.7}
        return cfg

    def _start(self):
        input_dir = self.in_edit.text()
        output_dir = self.out_edit.text()
        if not input_dir or not os.path.isdir(input_dir):
            self.status.showMessage("请选择有效的输入目录")
            return
        if not output_dir:
            output_dir = os.path.join(input_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        cfg = self._build_config()
        self.pb.setValue(0)
        self.log.clear()
        self.log.append(f"开始处理: {input_dir} -> {output_dir}")
        self.worker = Worker(input_dir, output_dir, cfg)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self.log.append)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.start()
        self.btn_start.setEnabled(False)

    def _on_progress(self, done, total):
        pct = (done / total * 100) if total else 0
        self.pb.setValue(int(pct))
        self.status.showMessage(f"处理中: {done}/{total}")

    def _on_done(self, results):
        ok = sum(1 for r in results if r["success"])
        self.log.append(f"完成：成功 {ok} / 失败 {len(results) - ok}")
        self.status.showMessage("处理完成")
        self.btn_start.setEnabled(True)

    def _cancel(self):
        if self.worker:
            self.worker.cancel()

    def run(self):
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        self.show()
        app.exec_()
