"""批量处理器：多线程并发处理，支持进度回调与取消。"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import iter_images
from .processor import process_image


class BatchProcessor:
    """批量图片处理调度器。"""

    def __init__(self, max_workers=None):
        self.max_workers = max_workers or 4
        self._cancel = threading.Event()
        self._pause = threading.Event()
        self._pause.set()  # 默认不暂停
        self._lock = threading.Lock()

    def cancel(self):
        self._cancel.set()

    def is_cancelled(self):
        return self._cancel.is_set()

    def pause(self):
        self._pause.clear()

    def resume(self):
        self._pause.set()

    def process(
        self,
        input_dir,
        output_dir,
        config,
        recursive=True,
        progress_callback=None,
        log_callback=None,
    ):
        """处理目录下所有图片。

        progress_callback(done, total)
        log_callback(message)
        返回结果列表。
        """
        self._cancel.clear()
        self._pause.set()

        files = list(iter_images(input_dir, recursive=recursive))
        total = len(files)
        results = []

        if total == 0:
            if log_callback:
                log_callback("未找到任何图片文件")
            return results

        if progress_callback:
            progress_callback(0, total)

        done = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self._safe_process, f, output_dir, config): f
                for f in files
            }
            for fut in as_completed(futures):
                if self._cancel.is_set():
                    # 取消尚未开始的任务
                    for pending in futures:
                        pending.cancel()
                    break

                # 暂停时阻塞
                self._pause.wait()

                fname = futures[fut]
                try:
                    res = fut.result()
                except Exception as exc:  # noqa: BLE001
                    res = {
                        "input": fname,
                        "output": None,
                        "success": False,
                        "error": str(exc),
                        "operations": [],
                        "input_size": 0,
                        "output_size": 0,
                    }
                results.append(res)
                done += 1
                if log_callback and res["success"]:
                    log_callback(
                        f"已完成 {res['operations']}: "
                        f"{_basename(fname)} -> {_basename(res['output'])}"
                    )
                elif log_callback and not res["success"]:
                    log_callback(f"失败 {_basename(fname)}: {res['error']}")
                if progress_callback:
                    progress_callback(done, total)

        if progress_callback:
            progress_callback(done, total)
        return results

    def _safe_process(self, path, output_dir, config):
        return process_image(path, output_dir, config)


def _basename(path):
    import os
    return os.path.basename(path) if path else ""
