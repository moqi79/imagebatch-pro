"""插件系统与圆角扩展测试。"""
from PIL import Image

from core.round_corner import RoundCornerProcessor
from plugins.base import Plugin
from plugins.examples.border_plugin import BorderPlugin
from plugins.examples.filter_plugin import FilterPlugin


def test_round_corner(sample_rgba_image):
    proc = RoundCornerProcessor(radius=20)
    out = proc.process(sample_rgba_image)
    assert out.mode == "RGBA"
    assert out.size == sample_rgba_image.size
    # 四个角应为透明
    assert out.getpixel((0, 0))[3] == 0


def test_border_plugin(sample_rgb_image):
    p = BorderPlugin(width=10, color="#000000")
    out = p.process(sample_rgb_image)
    assert out.size == (sample_rgb_image.size[0] + 20, sample_rgb_image.size[1] + 20)


def test_filter_grayscale(sample_rgb_image):
    p = FilterPlugin(effect="grayscale")
    out = p.process(sample_rgb_image)
    assert out.mode == "RGB"
    # 灰度图 R=G=B
    r, g, b = out.getpixel((50, 50))
    assert r == g == b


def test_filter_invert(sample_rgb_image):
    p = FilterPlugin(effect="invert")
    out = p.process(sample_rgb_image)
    assert out.size == sample_rgb_image.size


def test_filter_blur(sample_rgb_image):
    p = FilterPlugin(effect="blur")
    out = p.process(sample_rgb_image)
    assert out.size == sample_rgb_image.size


def test_filter_unknown_returns_original(sample_rgb_image):
    p = FilterPlugin(effect="nonexistent")
    out = p.process(sample_rgb_image)
    assert out.size == sample_rgb_image.size


def test_base_plugin_raises():
    class Bad(Plugin):
        name = "bad"
    try:
        Bad().process(Image.new("RGB", (10, 10)))
        assert False, "应抛出 NotImplementedError"
    except NotImplementedError:
        pass


def test_base_plugin_repr():
    class Foo(Plugin):
        name = "foo"
    assert "foo" in repr(Foo())
