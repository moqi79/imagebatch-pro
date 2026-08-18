"""处理流程编排器与预设测试。"""
import os
import json

from core.processor import ProcessingConfig, process_image
from core.utils import iter_images
from plugins.examples.border_plugin import BorderPlugin


def test_compress_only(input_dir, tmp_path):
    out_dir = tmp_path / "out_compress"
    cfg = ProcessingConfig(compress={"target_size_kb": 50, "min_quality": 40})
    files = list(iter_images(input_dir))
    for f in files:
        res = process_image(f, str(out_dir), cfg)
        assert res["success"], res.get("error")
        assert os.path.exists(res["output"])
        assert res["output_size"] <= 50 * 1024 + 1024
        assert "compress:" in " ".join(res["operations"])


def test_resize_only(input_dir, tmp_path):
    out_dir = tmp_path / "out_resize"
    cfg = ProcessingConfig(resize={"width": 100, "height": 100, "mode": "cover"})
    files = list(iter_images(input_dir))
    for f in files:
        res = process_image(f, str(out_dir), cfg)
        assert res["success"], res.get("error")
        from PIL import Image
        with Image.open(res["output"]) as img:
            assert img.size == (100, 100)


def test_convert_format(input_dir, tmp_path):
    out_dir = tmp_path / "out_convert"
    cfg = ProcessingConfig(convert={"format": "png", "quality": 85})
    cfg.output_format = "png"
    for f in list(iter_images(input_dir)):
        res = process_image(f, str(out_dir), cfg)
        assert res["success"]
        assert res["output"].endswith(".png")


def test_watermark(input_dir, tmp_path):
    out_dir = tmp_path / "out_wm"
    cfg = ProcessingConfig(watermark_text={
        "text": "@Test", "position": "bottom-right",
        "font_size": 36, "color": "#FFFFFF", "opacity": 0.7,
    })
    res = process_image(list(iter_images(input_dir))[0], str(out_dir), cfg)
    assert res["success"]
    assert "watermark:text" in res["operations"]


def test_plugin_in_chain(input_dir, tmp_path, monkeypatch):
    # 授权门控：插件需工作室版，测试中临时解锁
    from core.license import get_license_manager
    lm = get_license_manager()
    monkeypatch.setattr(lm, "_edition", "studio")
    monkeypatch.setattr(lm, "is_feature_unlocked", lambda f: True)

    out_dir = tmp_path / "out_plugin"
    cfg = ProcessingConfig(plugins=[BorderPlugin(width=15, color="#000000")])
    res = process_image(list(iter_images(input_dir))[0], str(out_dir), cfg)
    assert res["success"], res.get("error")
    assert "plugin:border" in res["operations"]


def test_failed_image(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    cfg = ProcessingConfig()
    res = process_image(str(bad), str(tmp_path / "out"), cfg)
    assert not res["success"]
    assert res["error"]


def test_from_preset():
    data = {
        "params": {
            "resize": {"width": 800, "height": 800, "mode": "cover"},
            "compress": {"target_size_kb": 300, "min_quality": 80},
            "watermark": {"text": "@X", "position": "bottom-right"},
            "format": "jpg",
        }
    }
    cfg = ProcessingConfig.from_preset(data)
    assert cfg.resize["width"] == 800
    assert cfg.compress["target_size_kb"] == 300
    assert cfg.watermark_text["text"] == "@X"
    assert cfg.convert["format"] == "jpg"
