"""批量处理器测试。"""
import os

from core.processor import ProcessingConfig
from core.batch import BatchProcessor


def test_batch_process_all(input_dir, tmp_path):
    out_dir = tmp_path / "batch_out"
    bp = BatchProcessor(max_workers=2)
    cfg = ProcessingConfig(
        resize={"width": 120, "height": 120, "mode": "cover"},
        compress={"target_size_kb": 30, "min_quality": 40},
    )
    results = bp.process(input_dir, str(out_dir), cfg)
    assert len(results) == 5
    assert all(r["success"] for r in results)
    assert all(os.path.exists(r["output"]) for r in results)


def test_batch_progress_callback(input_dir, tmp_path):
    out_dir = tmp_path / "batch_progress"
    bp = BatchProcessor(max_workers=3)
    cfg = ProcessingConfig(compress={"target_size_kb": 50, "min_quality": 40})
    seen = []
    bp.process(input_dir, str(out_dir), cfg,
               progress_callback=lambda d, t: seen.append((d, t)))
    assert seen[-1][0] == 5
    assert seen[-1][1] == 5


def test_batch_log_callback(input_dir, tmp_path):
    out_dir = tmp_path / "batch_log"
    bp = BatchProcessor(max_workers=2)
    cfg = ProcessingConfig()
    logs = []
    bp.process(input_dir, str(out_dir), cfg, log_callback=logs.append)
    assert len(logs) >= 5


def test_batch_empty_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    bp = BatchProcessor()
    results = bp.process(str(empty), str(tmp_path / "out"), ProcessingConfig())
    assert results == []
