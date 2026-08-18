"""压缩引擎测试。"""
from PIL import Image

from core.compressor import compress_to_size


def test_compress_under_target(sample_rgb_image):
    data, q = compress_to_size(sample_rgb_image, target_size_kb=20, min_quality=40)
    assert len(data) <= 20 * 1024
    assert 40 <= q <= 95


def test_compress_quality_in_range(sample_rgb_image):
    data, q = compress_to_size(sample_rgb_image, target_size_kb=5, min_quality=30)
    assert 30 <= q <= 95


def test_compress_zero_target(sample_rgb_image):
    data, q = compress_to_size(sample_rgb_image, target_size_kb=0, max_quality=90)
    assert q == 90
    assert len(data) > 0


def test_compress_rgba(sample_rgba_image):
    data, q = compress_to_size(sample_rgba_image, target_size_kb=30, min_quality=40)
    # RGBA 会被转 RGB
    assert len(data) <= 30 * 1024 + 1024  # 允许一点边界误差


def test_compress_webp(sample_rgb_image):
    data, q = compress_to_size(
        sample_rgb_image, target_size_kb=30, min_quality=40, fmt="WebP")
    assert len(data) > 0
