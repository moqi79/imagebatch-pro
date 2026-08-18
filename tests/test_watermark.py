"""水印引擎测试。"""
from PIL import Image

from core.watermark import add_text_watermark, add_image_watermark


def test_text_watermark_returns_image(sample_rgb_image):
    out = add_text_watermark(sample_rgb_image, "@Brand", position="bottom-right")
    assert out.size == sample_rgb_image.size


def test_text_watermark_all_positions(sample_rgb_image):
    positions = [
        "top-left", "top-center", "top-right", "center",
        "bottom-left", "bottom-center", "bottom-right", "random",
    ]
    for pos in positions:
        out = add_text_watermark(sample_rgb_image, "Test", position=pos)
        assert out.size == sample_rgb_image.size


def test_text_watermark_tile(sample_rgb_image):
    out = add_text_watermark(sample_rgb_image, "W", position="tile", tile_gap=80)
    assert out.size == sample_rgb_image.size


def test_text_watermark_empty_returns_same(sample_rgb_image):
    out = add_text_watermark(sample_rgb_image, "")
    assert out.size == sample_rgb_image.size


def test_text_watermark_rgba(sample_rgba_image):
    out = add_text_watermark(sample_rgba_image, "透明", position="center")
    assert out.mode in ("RGB", "RGBA")


def test_image_watermark_missing_path(sample_rgb_image):
    out = add_image_watermark(sample_rgb_image, "/no/such/file.png")
    # 路径不存在时应原样返回
    assert out.size == sample_rgb_image.size


def test_image_watermark_valid(tmp_path, sample_rgb_image):
    logo = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    logo_path = tmp_path / "logo.png"
    logo.save(logo_path, format="PNG")
    out = add_image_watermark(sample_rgb_image, str(logo_path), scale=0.2)
    assert out.size == sample_rgb_image.size
