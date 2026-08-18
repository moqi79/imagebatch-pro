"""插件基类：所有自定义处理流程插件继承此类。"""
from PIL import Image


class Plugin:
    """插件基类。

    子类需实现 :meth:`process`，并设置 :attr:`name`。
    """

    name = "base"
    description = "插件基类"

    def __init__(self, **options):
        self.options = options

    def process(self, image: Image.Image) -> Image.Image:
        """处理图片并返回新 Image。子类必须实现。"""
        raise NotImplementedError

    def __repr__(self):
        return f"<Plugin {self.name}>"
