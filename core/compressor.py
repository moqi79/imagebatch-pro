"""智能压缩引擎：在质量区间内二分查找最接近目标体积的参数。"""
from io import BytesIO
from PIL import Image

from .utils import image_to_bytes


def _save_bytes(img, quality):
    """以指定质量保存为 JPEG 字节。"""
    buf = BytesIO()
    save_img = img
    if img.mode == "RGBA":
        save_img = img.convert("RGB")
    save_img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def compress_to_size(
    image,
    target_size_kb,
    min_quality=40,
    max_quality=95,
    fmt="JPEG",
    step=1,
):
    """二分查找使输出体积 <= 目标大小的最高质量。

    返回 (bytes, final_quality)。若最低质量仍超出目标，返回最低质量结果
    （保证可用，仅记录 final_quality 供上层提示）。
    """
    if fmt.upper() != "JPEG":
        # 非 JPEG 格式（如 WebP）也支持 quality，复用同一逻辑
        return _compress_generic(image, target_size_kb, min_quality, max_quality, fmt)

    target_bytes = int(target_size_kb * 1024)
    if target_bytes <= 0:
        return image_to_bytes(image, fmt=fmt, quality=max_quality), max_quality

    lo, hi, best_q, best_b = min_quality, max_quality, min_quality, None
    while lo <= hi:
        mid = (lo + hi) // 2
        data = _save_bytes(image, mid)
        if len(data) <= target_bytes:
            best_q, best_b = mid, data
            lo = mid + 1  # 尝试更高质量
        else:
            hi = mid - 1

    if best_b is None:
        # 最低质量仍超限，返回最低质量结果
        best_b = _save_bytes(image, min_quality)
        best_q = min_quality
    return best_b, best_q


def _compress_generic(image, target_size_kb, min_quality, max_quality, fmt):
    """对 WebP 等支持 quality 的格式执行二分查找。"""
    target_bytes = int(target_size_kb * 1024)
    lo, hi, best_q, best_b = min_quality, max_quality, min_quality, None
    while lo <= hi:
        mid = (lo + hi) // 2
        data = image_to_bytes(image, fmt=fmt, quality=mid)
        if target_bytes <= 0 or len(data) <= target_bytes:
            best_q, best_b = mid, data
            lo = mid + 1
        else:
            hi = mid - 1
    if best_b is None:
        best_b = image_to_bytes(image, fmt=fmt, quality=min_quality)
        best_q = min_quality
    return best_b, best_q
