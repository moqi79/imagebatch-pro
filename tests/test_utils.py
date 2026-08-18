"""工具函数测试。"""
import os

from core.utils import (
    is_image_file, iter_images, format_file_size, hex_to_rgb,
    get_output_path, ensure_dir, image_to_bytes,
)
from PIL import Image
from io import BytesIO


def test_is_image_file():
    assert is_image_file("a.jpg")
    assert is_image_file("a.JPEG")
    assert is_image_file("path/to/x.webp")
    assert not is_image_file("a.txt")
    assert not is_image_file("a.mp4")


def test_iter_images(input_dir):
    files = list(iter_images(input_dir))
    assert len(files) == 5
    assert all(f.endswith(".jpg") for f in files)


def test_iter_images_non_recursive(input_dir):
    files = list(iter_images(input_dir, recursive=False))
    assert len(files) == 5


def test_format_file_size():
    assert "B" in format_file_size(500)
    assert "KB" in format_file_size(2048)
    assert "MB" in format_file_size(5 * 1024 * 1024)


def test_hex_to_rgb():
    assert hex_to_rgb("#FF0000") == (255, 0, 0)
    assert hex_to_rgb("#ffffff") == (255, 255, 255)
    assert hex_to_rgb("00FF00") == (0, 255, 0)
    assert hex_to_rgb("#F00") == (255, 0, 0)


def test_get_output_path_default(tmp_path):
    p = get_output_path(str(tmp_path / "photo.jpg"), str(tmp_path / "out"))
    assert p.endswith("photo.jpg")


def test_get_output_path_new_format(tmp_path):
    p = get_output_path(str(tmp_path / "photo.jpg"), str(tmp_path / "out"), "png")
    assert p.endswith("photo.png")


def test_ensure_dir(tmp_path):
    d = tmp_path / "a" / "b" / "c"
    ensure_dir(str(d))
    assert d.is_dir()


def test_image_to_bytes_jpeg(sample_rgb_image):
    data = image_to_bytes(sample_rgb_image, fmt="JPEG", quality=85)
    assert len(data) > 0
    assert Image.open(BytesIO(data)).format == "JPEG"


def test_image_to_bytes_rgba_to_jpeg(sample_rgba_image):
    data = image_to_bytes(sample_rgba_image, fmt="JPEG")
    img = Image.open(BytesIO(data))
    assert img.mode == "RGB"
