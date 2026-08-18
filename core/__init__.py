"""ImageBatch Pro 核心处理引擎。"""
from .compressor import compress_to_size
from .resizer import resize
from .watermark import add_text_watermark, add_image_watermark
from .converter import convert_image
from .processor import ProcessingConfig, process_image
from .batch import BatchProcessor
from .license import LicenseManager, get_license_manager

__all__ = [
    "compress_to_size",
    "resize",
    "add_text_watermark",
    "add_image_watermark",
    "convert_image",
    "ProcessingConfig",
    "process_image",
    "BatchProcessor",
    "LicenseManager",
    "get_license_manager",
]
