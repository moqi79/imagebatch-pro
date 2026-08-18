"""水印渲染引擎：文字水印与图片水印。"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

from config import get_cjk_font_path
from .utils import hex_to_rgb

# 9 宫格预设位置
POSITIONS = (
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
)


def _load_font(font_size, font_path=None):
    """加载字体，优先使用参数指定 > 系统中文字体 > 默认字体。"""
    path = font_path or get_cjk_font_path()
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, font_size)
        except Exception:
            pass
    return ImageFont.load_default()


def _position_box(canvas_size, layer_size, position, margin=10):
    """根据位置名称计算左上角坐标。"""
    cw, ch = canvas_size
    lw, lh = layer_size
    margin = max(0, margin)
    pos = (position or "bottom-right").lower()

    if pos == "tile" or pos == "random":
        return (0, 0)

    x = y = margin
    if "right" in pos:
        x = cw - lw - margin
    elif "center" in pos and "left" not in pos and "right" not in pos:
        x = (cw - lw) // 2
    if "bottom" in pos:
        y = ch - lh - margin
    elif "center" in pos and "top" not in pos and "bottom" not in pos:
        y = (ch - lh) // 2
    # 处理 center-left / center-right
    if pos in ("center-left", "center-right", "center"):
        y = (ch - lh) // 2
    if pos in ("top-center", "bottom-center"):
        x = (cw - lw) // 2
    return (max(0, x), max(0, y))


def _hex_to_rgba(color, opacity):
    """#RRGGBB + opacity(0~1) -> (R,G,B,A int 0~255)。"""
    r, g, b = hex_to_rgb(color)
    return (r, g, b, int(255 * max(0.0, min(1.0, opacity))))


def add_text_watermark(
    image,
    text,
    position="bottom-right",
    font_size=36,
    color="#FFFFFF",
    opacity=0.7,
    font_path=None,
    margin=10,
    tile_gap=120,
    rotation=0,
):
    """在图片上添加文字水印。"""
    if not text:
        return image

    base = image.convert("RGBA")
    txt_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    font = _load_font(font_size, font_path)
    fill = _hex_to_rgba(color, opacity)

    pos = (position or "bottom-right").lower()
    # 计算单行文字尺寸（兼容 Pillow 9/10）
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = font.getsize(text)

    if pos == "tile":
        _draw_tile(draw, text, font, fill, base.size, tw, th, tile_gap, rotation)
    elif pos == "random":
        x = random.randint(0, max(0, base.size[0] - tw))
        y = random.randint(0, max(0, base.size[1] - th))
        _draw_text(draw, text, font, fill, x, y, rotation)
    else:
        x, y = _position_box(base.size, (tw, th), pos, margin)
        _draw_text(draw, text, font, fill, x, y, rotation)

    return Image.alpha_composite(base, txt_layer).convert(
        "RGB" if image.mode == "RGB" else "RGBA"
    )


def _draw_text(draw, text, font, fill, x, y, rotation):
    """绘制单条文字（支持旋转）。"""
    if rotation:
        from PIL import Image as _Image
        tmp = _Image.new("RGBA", draw.textbbox((0, 0), text, font=font)[2:], (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((0, 0), text, font=font, fill=fill)
        tmp = tmp.rotate(rotation, expand=True)
        draw.bitmap((x, y), tmp)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def _draw_tile(draw, text, font, fill, canvas_size, tw, th, gap, rotation):
    """平铺水印。"""
    cw, ch = canvas_size
    step_x = max(tw + 20, gap)
    step_y = max(th + 20, gap)
    y = -step_y
    while y < ch + step_y:
        x = -step_x
        offset = step_x // 2 if (y // step_y) % 2 else 0
        while x < cw + step_x:
            draw.text((x + offset, y), text, font=font, fill=fill)
            x += step_x
        y += step_y


def add_image_watermark(
    image,
    watermark_path,
    position="bottom-right",
    scale=0.2,
    opacity=0.8,
    margin=10,
    tile=False,
):
    """在图片上叠加图片水印（Logo）。"""
    if not watermark_path or not os.path.exists(watermark_path):
        return image

    wm = Image.open(watermark_path).convert("RGBA")
    base = image.convert("RGBA")
    bw, bh = base.size

    if scale and scale < 1:
        scale = scale
    elif scale >= 1:
        scale = scale / max(base.size) if base.size else 0.2
    new_w = max(1, int(base.size[0] * scale))
    wm = wm.resize(
        (new_w, max(1, int(new_w * wm.size[1] / max(1, wm.size[0])))),
        Image.LANCZOS,
    )

    # 应用透明度
    if opacity < 1.0:
        wm = _apply_opacity(wm, opacity)

    wm_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if tile:
        gap_x = wm.size[0] + 40
        gap_y = wm.size[1] + 40
        y = 0
        while y < bh + gap_y:
            x = 0
            offset = gap_x // 2 if (y // gap_y) % 2 else 0
            while x < bw + gap_x:
                wm_layer.paste(wm, (x + offset, y), wm)
                x += gap_x
            y += gap_y
    else:
        x, y = _position_box(base.size, wm.size, position, margin)
        wm_layer.paste(wm, (x, y), wm)

    return Image.alpha_composite(base, wm_layer).convert(
        "RGB" if image.mode == "RGB" else "RGBA"
    )


def _apply_opacity(image, opacity):
    """对带 alpha 的图片整体降低透明度。"""
    r, g, b, a = image.split()
    a = a.point(lambda v: int(v * opacity))
    return Image.merge("RGBA", (r, g, b, a))
