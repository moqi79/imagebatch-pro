"""格式转换器。"""
from PIL import Image

from config import FORMAT_PIL_MAP, NO_ALPHA_FORMATS
from .utils import image_to_bytes


def convert_image(image, target_format, quality=85, keep_alpha=True):
    """将图片转换为目标格式，返回序列化字节。

    - target_format: jpg/png/webp/bmp/tiff
    - keep_alpha: 仅对支持透明的格式保留 alpha 通道
    """
    fmt = (target_format or "jpg").lower().lstrip(".")
    pil_fmt = FORMAT_PIL_MAP.get(fmt, "JPEG")
    img = image

    if fmt in NO_ALPHA_FORMATS:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
    elif not keep_alpha:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
    else:
        if fmt == "png" and img.mode not in ("RGBA", "RGB", "L", "P"):
            img = img.convert("RGBA")

    return image_to_bytes(img, fmt=pil_fmt, quality=quality), fmt
