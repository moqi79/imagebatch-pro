"""格式转换器测试。"""
from PIL import Image
from io import BytesIO

from core.converter import convert_image


def _to_image(data, fmt):
    return Image.open(BytesIO(data))


def test_convert_to_png(sample_rgb_image):
    data, fmt = convert_image(sample_rgb_image, "png")
    assert fmt == "png"
    img = _to_image(data, "png")
    assert img.format == "PNG"


def test_convert_to_webp(sample_rgb_image):
    data, fmt = convert_image(sample_rgb_image, "webp", quality=80)
    img = _to_image(data, "webp")
    assert img.format == "WEBP"


def test_convert_rgba_to_jpg_flattens(sample_rgba_image):
    data, fmt = convert_image(sample_rgba_image, "jpg")
    img = _to_image(data, "jpg")
    assert img.mode == "RGB"
    assert img.format == "JPEG"


def test_convert_to_bmp(sample_rgb_image):
    data, fmt = convert_image(sample_rgb_image, "bmp")
    img = _to_image(data, "bmp")
    assert img.format == "BMP"


def test_convert_default_format(sample_rgb_image):
    data, fmt = convert_image(sample_rgb_image, "")
    assert fmt == "jpg"
