"""尺寸调整引擎测试。"""
from core.resizer import resize


def test_cover_mode(sample_rgb_image):
    out = resize(sample_rgb_image, 100, 100, mode="cover")
    assert out.size == (100, 100)


def test_stretch_mode(sample_rgb_image):
    out = resize(sample_rgb_image, 120, 80, mode="stretch")
    assert out.size == (120, 80)


def test_contain_mode_keeps_aspect(sample_rgb_image):
    out = resize(sample_rgb_image, 200, 100, mode="contain", background="#000000")
    assert out.size == (200, 100)
    # 左上角应为背景色（黑）
    assert out.getpixel((0, 0))[:3] == (0, 0, 0)


def test_single_width(sample_rgb_image):
    out = resize(sample_rgb_image, 200, 0)
    assert out.size[0] == 200


def test_single_height(sample_rgb_image):
    out = resize(sample_rgb_image, 0, 150)
    assert out.size[1] == 150


def test_pad_mode(sample_rgb_image):
    out = resize(sample_rgb_image, 500, 500, mode="pad", background="#FF0000")
    assert out.size == (500, 500)


def test_gravity_offsets(sample_rgb_image):
    top = resize(sample_rgb_image, 100, 100, mode="cover", gravity="top-left")
    bot = resize(sample_rgb_image, 100, 100, mode="cover", gravity="bottom-right")
    assert top.size == bot.size == (100, 100)
