"""EXIF 元数据编辑器（专业版）。

依赖可选库 exifread / piexif；未安装时降级为 Pillow 内置能力。
"""
from io import BytesIO

from PIL import Image

try:
    import piexif
    _HAS_PIEXIF = True
except ImportError:
    piexif = None
    _HAS_PIEXIF = False

try:
    import exifread
    _HAS_EXIFREAD = True
except ImportError:
    exifread = None
    _HAS_EXIFREAD = False


def read_exif(path):
    """读取图片 EXIF 信息，返回字典。"""
    if _HAS_EXIFREAD:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        return {str(k): str(v) for k, v in tags.items()}

    # 降级：用 Pillow 读取
    exif_data = {}
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if exif:
                exif_data = {str(k): str(v) for k, v in exif.items()}
    except Exception:
        pass
    return exif_data


def clear_exif(image):
    """清除图片所有 EXIF 元数据，返回新 Image。"""
    data = list(image.getdata())
    clean = Image.new(image.mode, image.size)
    clean.putdata(data)
    return clean


def set_exif(image, exif_dict):
    """写入 EXIF 元数据（需 piexif），返回序列化字节（JPEG）。"""
    if not _HAS_PIEXIF:
        raise RuntimeError("piexif 未安装，无法写入 EXIF")

    if image.mode == "RGBA":
        image = image.convert("RGB")
    exif_bytes = piexif.dump(exif_dict)
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=95, exif=exif_bytes)
    return buf.getvalue()


def available():
    """返回已安装的 EXIF 能力。"""
    return {"exifread": _HAS_EXIFREAD, "piexif": _HAS_PIEXIF}
