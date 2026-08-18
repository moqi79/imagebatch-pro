"""圆角裁剪扩展（二次开发示例）。"""
from PIL import Image, ImageDraw


class RoundCornerProcessor:
    def __init__(self, radius=30):
        self.radius = radius

    def process(self, image):
        """将图片裁剪为圆角矩形，返回 RGBA Image。"""
        image = image.convert("RGBA")
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), image.size], radius=self.radius, fill=255)
        output = Image.new("RGBA", image.size, (0, 0, 0, 0))
        output.paste(image, (0, 0), mask)
        return output
