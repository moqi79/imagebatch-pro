"""pytest 共享夹具。"""
import os
import sys

import pytest
from PIL import Image, ImageDraw

# 确保项目根目录在 sys.path 中
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def sample_rgb_image():
    """一张带渐变的 400x300 RGB 图片。"""
    img = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for x in range(400):
        for y in range(0, 300, 3):
            draw.line([(x, y), (x, y + 2)], fill=(x % 256, y % 256, (x + y) % 256))
    return img


@pytest.fixture
def sample_rgba_image():
    """一张带透明区域的 RGBA 图片。"""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 180, 180], fill=(255, 0, 0, 255))
    draw.rectangle([80, 80, 120, 120], fill=(0, 0, 0, 0))
    return img


@pytest.fixture
def tmp_image_file(tmp_path, sample_rgb_image):
    """写入临时目录的 JPG 图片。"""
    p = tmp_path / "test_img.jpg"
    sample_rgb_image.save(p, format="JPEG", quality=90)
    return str(p)


@pytest.fixture
def tmp_png_file(tmp_path, sample_rgba_image):
    """写入临时目录的 PNG 图片。"""
    p = tmp_path / "test_alpha.png"
    sample_rgba_image.save(p, format="PNG")
    return str(p)


@pytest.fixture
def input_dir(tmp_path, sample_rgb_image):
    """包含若干图片的输入目录。"""
    d = tmp_path / "input"
    d.mkdir()
    for i in range(5):
        img = sample_rgb_image.resize((300 + i * 10, 250 + i * 10))
        img.save(d / f"img_{i:02d}.jpg", format="JPEG", quality=85)
    return str(d)
