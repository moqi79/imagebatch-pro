"""边框插件：为图片添加纯色边框。"""
from PIL import Image, ImageOps

from ..base import Plugin


class BorderPlugin(Plugin):
    name = "border"
    description = "添加纯色边框"

    def __init__(self, width=10, color="#000000"):
        super().__init__(width=width, color=color)
        self.border_width = width
        self.color = color

    def process(self, image: Image.Image) -> Image.Image:
        return ImageOps.expand(image, border=self.border_width, fill=self.color)
