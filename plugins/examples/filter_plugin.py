"""滤镜插件：灰度 / 反色 / 模糊。"""
from PIL import Image, ImageFilter

from ..base import Plugin


class FilterPlugin(Plugin):
    name = "filter"
    description = "滤镜效果（灰度/反色/模糊）"

    def __init__(self, effect="grayscale"):
        super().__init__(effect=effect)
        self.effect = effect

    def process(self, image: Image.Image) -> Image.Image:
        if self.effect == "grayscale":
            return image.convert("L").convert("RGB")
        if self.effect == "invert":
            return Image.eval(image.convert("RGB"), lambda v: 255 - v)
        if self.effect == "blur":
            return image.filter(ImageFilter.GaussianBlur(radius=2))
        if self.effect == "sharpen":
            return image.filter(ImageFilter.SHARPEN)
        return image
