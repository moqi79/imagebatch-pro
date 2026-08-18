"""Web UI 服务器——双击 exe 时自动启动浏览器界面。

基于 Python 内置 http.server，无需 tkinter/PyQt 等额外依赖。
启动后自动打开默认浏览器。
"""
import os
import sys
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import config
from core.processor import ProcessingConfig, process_image
from core.batch import BatchProcessor
from core.utils import iter_images, format_file_size
from core.license import get_license_manager, LicenseManager
from core.payment import (
    generate_order, confirm_payment, PRICING,
    format_order_text, get_pending_orders,
)


def load_presets():
    """加载预设模板。"""
    presets_dir = os.path.join(BASE_DIR, "assets", "presets")
    if getattr(sys, "frozen", False):
        presets_dir = os.path.join(sys._MEIPASS, "assets", "presets")
    presets = {}
    if not os.path.isdir(presets_dir):
        return presets
    for fname in os.listdir(presets_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(presets_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pid = fname.replace(".json", "")
            presets[pid] = data
        except (json.JSONDecodeError, OSError):
            continue
    return presets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web_ui")


class APIHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器。"""

    def log_message(self, *args):
        pass  # 静默日志

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 静态文件
        if path == "/" or path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self._serve_file("style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._serve_file("app.js", "application/javascript; charset=utf-8")
        # API 端点
        elif path == "/api/status":
            self._api_status()
        elif path == "/api/presets":
            self._api_presets()
        elif path == "/api/orders":
            self._api_orders()
        elif path == "/api/machine-id":
            self._api_machine_id()
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/select-dir":
            self._api_select_dir(body)
        elif path == "/api/process":
            self._api_process(body)
        elif path == "/api/pay":
            self._api_pay(body)
        elif path == "/api/confirm-payment":
            self._api_confirm_payment(body)
        elif path == "/api/deactivate":
            self._api_deactivate()
        else:
            self._json(404, {"error": "not found"})

    # ---- 静态文件 ----
    def _serve_file(self, filename, content_type):
        filepath = os.path.join(WEB_DIR, filename)
        if not os.path.exists(filepath):
            # 打包后资源在 _MEIPASS
            if getattr(sys, "frozen", False):
                base = sys._MEIPASS
                filepath = os.path.join(base, "web_ui", filename)
        if not os.path.exists(filepath):
            self.send_error(404)
            return
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    # ---- 工具 ----
    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # ---- API ----
    def _api_status(self):
        lm = get_license_manager()
        feats = sorted(lm.get_unlocked_features())
        from core.license import FEATURE_NAMES
        self._json(200, {
            "edition": lm.edition,
            "is_activated": lm.is_activated,
            "summary": lm.summary(),
            "features": [{"key": f, "name": FEATURE_NAMES.get(f, f)} for f in feats],
            "version": config.__version__,
            "pricing": {k: v for k, v in PRICING.items()},
        })

    def _api_presets(self):
        presets = load_presets()
        self._json(200, {"presets": presets})

    def _api_orders(self):
        orders = get_pending_orders()
        self._json(200, {"orders": orders})

    def _api_machine_id(self):
        lm = get_license_manager()
        self._json(200, {"machine_id": lm.machine_id})

    def _api_pay(self, body):
        edition = body.get("edition", "pro")
        if edition not in PRICING:
            self._json(400, {"error": "无效版本"})
            return
        order = generate_order(edition)
        self._json(200, {"order": order, "text": format_order_text(order)})

    def _api_confirm_payment(self, body):
        code = body.get("code", "")
        success, message, key = confirm_payment(code)
        self._json(200 if success else 400, {
            "success": success,
            "message": message,
            "license_key": key,
        })

    def _api_deactivate(self):
        lm = get_license_manager()
        lm.deactivate()
        self._json(200, {"success": True})

    def _api_select_dir(self, body):
        """扫描目录中的图片文件。"""
        dir_path = body.get("path", "")
        if not dir_path or not os.path.isdir(dir_path):
            self._json(400, {"error": "目录不存在"})
            return
        files = []
        for f in iter_images(dir_path):
            files.append({
                "name": os.path.basename(f),
                "path": f,
                "size": os.path.getsize(f),
            })
        self._json(200, {"files": files, "count": len(files)})

    def _api_process(self, body):
        """处理图片。"""
        input_dir = body.get("input_dir", "")
        output_dir = body.get("output_dir", "")
        if not input_dir or not os.path.isdir(input_dir):
            self._json(400, {"error": "输入目录无效"})
            return
        if not output_dir:
            output_dir = os.path.join(input_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        cfg = ProcessingConfig()

        # 压缩
        compress = body.get("compress")
        if compress and compress > 0:
            cfg.compress = {"target_size_kb": compress, "min_quality": 40}

        # 改尺寸
        resize = body.get("resize")
        if resize and resize.get("width") and resize.get("height"):
            cfg.resize = {
                "width": resize["width"],
                "height": resize["height"],
                "mode": resize.get("mode", "cover"),
                "background": resize.get("background", "#FFFFFF"),
                "gravity": resize.get("gravity", "center"),
            }

        # 格式转换
        fmt = body.get("format")
        if fmt and fmt != "original":
            cfg.convert = {"format": fmt, "quality": 85, "keep_alpha": True}
            cfg.output_format = fmt

        # 水印
        wm = body.get("watermark")
        if wm and wm.get("text"):
            cfg.watermark_text = {
                "text": wm["text"],
                "position": wm.get("position", "bottom-right"),
                "font_size": wm.get("size", 36),
                "color": wm.get("color", "#FFFFFF"),
                "opacity": wm.get("opacity", 0.7),
            }

        # 清除 EXIF
        if body.get("clear_exif"):
            cfg.exif_action = "clear"

        # 预设
        preset_name = body.get("preset")
        if preset_name:
            presets = load_presets()
            if preset_name in presets:
                cfg = ProcessingConfig.from_preset(presets[preset_name])

        # 处理
        files = list(iter_images(input_dir))
        if not files:
            self._json(400, {"error": "未找到图片文件"})
            return

        processor = BatchProcessor(max_workers=body.get("workers", 4))
        results = processor.process_batch(
            files, output_dir, cfg, progress_callback=None
        )

        success = sum(1 for r in results if r["success"])
        total_in = sum(r["input_size"] for r in results)
        total_out = sum(r["output_size"] for r in results if r["success"])
        ratio = (total_out / total_in * 100) if total_in else 0

        self._json(200, {
            "total": len(results),
            "success": success,
            "failed": len(results) - success,
            "input_size": total_in,
            "output_size": total_out,
            "ratio": round(ratio, 1),
            "results": [{
                "name": r["filename"],
                "success": r["success"],
                "input_size": r["input_size"],
                "output_size": r["output_size"],
                "error": r.get("error", ""),
            } for r in results],
        })


def find_free_port():
    """找到一个可用端口。"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_server(open_browser=True):
    """启动 Web UI 服务器。"""
    port = find_free_port()
    server = HTTPServer(("127.0.0.1", port), APIHandler)

    url = f"http://127.0.0.1:{port}"
    print(f"ImageBatch Pro v{config.__version__} 服务已启动")
    print(f"访问地址: {url}")
    print(f"按 Ctrl+C 退出")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()
