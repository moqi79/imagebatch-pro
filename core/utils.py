"""通用工具函数。"""
import os
import sys
import logging
from io import BytesIO

from PIL import Image, ImageOps

from config import READ_FORMATS

logger = logging.getLogger("imagebatch")


def setup_logging(level=logging.INFO):
    """配置日志输出。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)
    return logger


def is_image_file(path):
    """判断文件是否为受支持的图片（依据扩展名）。"""
    ext = os.path.splitext(path)[1].lower()
    return ext in READ_FORMATS


def iter_images(directory, recursive=True):
    """遍历目录中的所有图片文件。"""
    if not os.path.isdir(directory):
        return
    if recursive:
        for root, _dirs, files in os.walk(directory):
            for f in sorted(files):
                p = os.path.join(root, f)
                if is_image_file(p):
                    yield p
    else:
        for f in sorted(os.listdir(directory)):
            p = os.path.join(directory, f)
            if os.path.isfile(p) and is_image_file(p):
                yield p


def open_image(path):
    """打开图片并自动修正 EXIF 朝向，返回 RGB/RGBA Image。"""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def image_to_bytes(img, fmt="JPEG", quality=85, **kwargs):
    """将 Image 序列化为字节。"""
    buf = BytesIO()
    save_img = img
    save_fmt = fmt
    save_kwargs = dict(kwargs)

    if fmt.upper() in ("JPEG", "BMP") and img.mode == "RGBA":
        save_img = img.convert("RGB")
    if fmt.upper() == "JPEG":
        save_kwargs.setdefault("quality", quality)
        save_kwargs.setdefault("optimize", True)
    save_img.save(buf, format=save_fmt, **save_kwargs)
    return buf.getvalue()


def format_file_size(num_bytes):
    """将字节数格式化为易读字符串。"""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


def ensure_dir(path):
    """确保目录存在。"""
    if path:
        os.makedirs(path, exist_ok=True)
    return path


def get_output_path(input_path, output_dir, target_format=None, suffix=""):
    """根据输入路径生成输出路径，保持相对目录结构。"""
    rel = os.path.basename(input_path)
    name, _ = os.path.splitext(rel)
    if target_format:
        target_format = target_format.lower().lstrip(".")
        ext = "jpg" if target_format in ("jpg", "jpeg") else target_format
    else:
        ext = os.path.splitext(rel)[1].lstrip(".")
        if not ext:
            ext = "jpg"
    new_name = f"{name}{suffix}.{ext}"
    return os.path.join(output_dir, new_name)


def hex_to_rgb(color):
    """将 #RRGGBB 或 #RGB 转为 (R, G, B) 元组。"""
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
