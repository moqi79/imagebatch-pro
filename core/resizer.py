"""尺寸调整引擎。

裁剪模式：
- contain  等比缩放至完整放入目标框，不足方向留白（背景填充）
- cover    等比缩放至完全覆盖目标框，超出方向居中裁剪（智能裁剪）
- stretch  强制拉伸至目标尺寸（可能变形）
- pad      等比缩放至较长边贴合，不足方向用指定颜色填充
"""
from PIL import Image

from .utils import hex_to_rgb


def resize(image, width, height, mode="cover", background="#FFFFFF", gravity="center"):
    """按模式调整尺寸，返回新 Image。"""
    if not width or not height:
        return _scale_single(image, width, height)

    mode = (mode or "cover").lower()
    if mode == "stretch":
        return image.resize((width, height), Image.LANCZOS)

    if mode == "contain":
        return _contain(image, width, height, background)

    if mode == "pad":
        scaled = _contain(image, width, height, background)
        return scaled

    # cover（默认）：覆盖裁剪
    return _cover(image, width, height, gravity)


def _scale_single(image, width, height):
    """仅指定宽或高时按比例缩放。"""
    orig_w, orig_h = image.size
    if width and not height:
        h = int(orig_h * width / orig_w)
        return image.resize((width, h), Image.LANCZOS)
    if height and not width:
        w = int(orig_w * height / orig_h)
        return image.resize((w, height), Image.LANCZOS)
    return image


def _cover(image, width, height, gravity):
    """覆盖裁剪：等比放大至完全覆盖，居中（或按 gravity）裁剪。"""
    orig_w, orig_h = image.size
    ratio = max(width / orig_w, height / orig_h)
    new_w, new_h = max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio))
    scaled = image.resize((new_w, new_h), Image.LANCZOS)

    offset = _gravity_offset(new_w, new_h, width, height, gravity)
    return scaled.crop((offset[0], offset[1], offset[0] + width, offset[1] + height))


def _contain(image, width, height, background):
    """等比放入并居中，留白处用背景色填充。"""
    orig_w, orig_h = image.size
    ratio = min(width / orig_w, height / orig_h)
    new_w, new_h = max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio))
    scaled = image.resize((new_w, new_h), Image.LANCZOS)

    bg = hex_to_rgb(background) if isinstance(background, str) else tuple(background)
    base_mode = "RGBA" if image.mode == "RGBA" else "RGB"
    canvas = Image.new(base_mode, (width, height), bg)
    offset = ((width - new_w) // 2, (height - new_h) // 2)
    canvas.paste(scaled, offset, scaled if base_mode == "RGBA" else None)
    return canvas


def _gravity_offset(src_w, src_h, dst_w, dst_h, gravity):
    """根据 gravity 计算裁剪偏移。"""
    g = (gravity or "center").lower()
    x = (src_w - dst_w) // 2
    y = (src_h - dst_h) // 2
    if "left" in g:
        x = 0
    elif "right" in g:
        x = src_w - dst_w
    if "top" in g:
        y = 0
    elif "bottom" in g:
        y = src_h - dst_h
    return (max(0, x), max(0, y))
