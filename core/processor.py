"""处理流程编排器：将单个图片按配置依次经过各处理引擎。"""
import os
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from config import NO_ALPHA_FORMATS, FORMAT_PIL_MAP
from .utils import open_image, image_to_bytes, ensure_dir, get_output_path
from .compressor import compress_to_size
from .resizer import resize as resize_image
from .watermark import add_text_watermark, add_image_watermark
from .converter import convert_image
from . import exif_editor
from .license import get_license_manager


@dataclass
class ProcessingConfig:
    """单次处理任务的全部参数。"""
    compress: dict = field(default_factory=dict)        # {target_size_kb, min_quality}
    resize: dict = field(default_factory=dict)        # {width, height, mode, background, gravity}
    convert: dict = field(default_factory=dict)       # {format, quality, keep_alpha}
    watermark_text: dict = field(default_factory=dict) # {text, position, font_size, color, opacity, font_path, margin, tile_gap, rotation}
    watermark_image: dict = field(default_factory=dict)  # {path, position, scale, opacity, margin, tile}
    exif_action: str = "keep"                          # keep | clear | set
    exif_dict: dict = field(default_factory=dict)
    round_corner: dict = field(default_factory=dict)   # {enabled, radius}
    plugins: list = field(default_factory=list)        # 插件实例列表
    output_format: str = ""                            # 最终输出格式（覆盖 convert.format）
    suffix: str = ""

    @classmethod
    def from_preset(cls, preset_data):
        """从预设 JSON 构建配置。"""
        params = preset_data.get("params", {})
        cfg = cls()
        if params.get("resize"):
            cfg.resize = dict(params["resize"])
        if params.get("compress"):
            cfg.compress = dict(params["compress"])
        if params.get("watermark"):
            wm = params["watermark"]
            cfg.watermark_text = {
                "text": wm.get("text", ""),
                "position": wm.get("position", "bottom-right"),
                "font_size": wm.get("font_size", 36),
                "color": wm.get("color", "#FFFFFF"),
                "opacity": wm.get("opacity", 0.7),
            }
        if params.get("format"):
            cfg.convert = {"format": params["format"]}
        return cfg


def process_image(input_path, output_dir, config):
    """处理单张图片，返回结果字典。"""
    result = {
        "input": input_path,
        "output": None,
        "input_size": os.path.getsize(input_path),
        "output_size": 0,
        "operations": [],
        "success": False,
        "error": None,
    }

    try:
        img = open_image(input_path)
        original_mode = img.mode

        # 1. 尺寸调整
        if config.resize and (config.resize.get("width") or config.resize.get("height")):
            r = config.resize
            img = resize_image(
                img,
                r.get("width", 0),
                r.get("height", 0),
                mode=r.get("mode", "cover"),
                background=r.get("background", "#FFFFFF"),
                gravity=r.get("gravity", "center"),
            )
            result["operations"].append(f"resize:{r.get('mode', 'cover')}")

        # 2. 圆角
        if config.round_corner.get("enabled"):
            from .round_corner import RoundCornerProcessor
            img = RoundCornerProcessor(config.round_corner.get("radius", 30)).process(img)
            result["operations"].append("round_corner")

        # 3. 插件处理（工作室版功能）
        _lm = get_license_manager()
        if config.plugins and not _lm.is_feature_unlocked("plugins"):
            result["error"] = "插件系统需要工作室版授权"
            return result
        for plugin in config.plugins:
            img = plugin.process(img)
            result["operations"].append(f"plugin:{plugin.name}")

        # 4. 文字水印
        wt = config.watermark_text
        if wt and wt.get("text"):
            img = add_text_watermark(
                img,
                wt["text"],
                position=wt.get("position", "bottom-right"),
                font_size=wt.get("font_size", 36),
                color=wt.get("color", "#FFFFFF"),
                opacity=wt.get("opacity", 0.7),
                font_path=wt.get("font_path"),
                margin=wt.get("margin", 10),
                tile_gap=wt.get("tile_gap", 120),
                rotation=wt.get("rotation", 0),
            )
            result["operations"].append("watermark:text")

        # 5. 图片水印（专业版功能）
        wi = config.watermark_image
        if wi and wi.get("path") and os.path.exists(wi["path"]):
            if not _lm.is_feature_unlocked("watermark_image"):
                result["error"] = "图片水印需要专业版授权"
                return result
            img = add_image_watermark(
                img,
                wi["path"],
                position=wi.get("position", "bottom-right"),
                scale=wi.get("scale", 0.2),
                opacity=wi.get("opacity", 0.8),
                margin=wi.get("margin", 10),
                tile=wi.get("tile", False),
            )
            result["operations"].append("watermark:image")

        # 6. 决定输出格式与字节
        out_fmt = (config.output_format or config.convert.get("format") or "jpg").lower().lstrip(".")
        target_kb = config.compress.get("target_size_kb")
        min_q = config.compress.get("min_quality", 40)
        quality = config.convert.get("quality", 85)

        data = _finalize_output(
            img, out_fmt, target_kb, min_q, quality, config, result
        )

        # 7. 写入文件
        ensure_dir(output_dir)
        out_path = get_output_path(input_path, output_dir, out_fmt, suffix=config.suffix)
        with open(out_path, "wb") as f:
            f.write(data)

        result["output"] = out_path
        result["output_size"] = len(data)
        result["success"] = True
        return result

    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result


def _finalize_output(img, out_fmt, target_kb, min_q, quality, config, result):
    """决定最终字节：压缩优先用二分查找，否则直接转换。"""
    pil_fmt = FORMAT_PIL_MAP.get(out_fmt, "JPEG")

    # JPEG/BMP 不支持透明，转为 RGB
    if out_fmt in NO_ALPHA_FORMATS and img.mode == "RGBA":
        img = img.convert("RGB")

    # EXIF 处理（仅 JPEG，专业版功能）
    exif_action = config.exif_action
    _lm = get_license_manager()
    if exif_action in ("clear", "set") and not _lm.is_feature_unlocked("exif"):
        result["error"] = "EXIF 编辑需要专业版授权"
        return b""
    if exif_action == "clear" and out_fmt in ("jpg", "jpeg"):
        img = exif_editor.clear_exif(img)
        result["operations"].append("exif:clear")

    if target_kb and target_kb > 0 and pil_fmt in ("JPEG", "WebP"):
        data, final_q = compress_to_size(
            img, target_kb, min_quality=min_q, max_quality=95, fmt=pil_fmt
        )
        result["operations"].append(f"compress:{final_q}q")
        return data

    if exif_action == "set" and out_fmt in ("jpg", "jpeg"):
        try:
            data = exif_editor.set_exif(img, config.exif_dict)
            result["operations"].append("exif:set")
            return data
        except RuntimeError:
            pass

    data, _ = convert_image(img, out_fmt, quality=quality,
                           keep_alpha=config.convert.get("keep_alpha", True))
    if out_fmt not in NO_ALPHA_FORMATS and out_fmt != "jpg":
        result["operations"].append(f"convert:{out_fmt}")
    else:
        result["operations"].append(f"convert:{out_fmt}")
    return data
