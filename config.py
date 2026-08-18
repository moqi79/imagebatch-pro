"""ImageBatch Pro 全局配置。"""
import os
import sys
import platform

__version__ = "1.0.0"
APP_NAME = "ImageBatch Pro"

# ---- 版本分级 ----
COMMUNITY = "community"
PRO = "pro"
STUDIO = "studio"
EDITIONS = (COMMUNITY, PRO, STUDIO)


def detect_edition():
    """根据已安装的依赖自动判断可用版本。"""
    try:
        import PyQt5  # noqa: F401
        import exifread  # noqa: F401
        return PRO
    except ImportError:
        try:
            import tkinter  # noqa: F401
            return COMMUNITY
        except ImportError:
            return COMMUNITY


# ---- 路径常量 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
PRESETS_DIR = os.path.join(ASSETS_DIR, "presets")

# ---- 处理默认参数 ----
MAX_WORKERS = min(8, (os.cpu_count() or 4))
BATCH_SIZE = 50
MEMORY_LIMIT_MB = 512

# ---- 支持的格式 ----
READ_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
WRITE_FORMATS = ["jpg", "png", "webp", "bmp", "tiff"]

FORMAT_PIL_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WebP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
}

# JPEG 不支持透明通道
NO_ALPHA_FORMATS = {"jpg", "jpeg", "bmp"}


def get_cjk_font_path():
    """返回系统上一个可用的中文字体路径，找不到返回 None。"""
    candidates = []
    if sys.platform == "win32":
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
    local_font = os.path.join(FONTS_DIR, "NotoSansCJK-Regular.otf")
    if os.path.exists(local_font):
        return local_font
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


# ---- 颜色预设 ----
THEME_LIGHT = {
    "bg": "#f5f5f5",
    "fg": "#222222",
    "accent": "#2563eb",
}

THEME_DARK = {
    "bg": "#1e1e1e",
    "fg": "#e0e0e0",
    "accent": "#3b82f6",
}
