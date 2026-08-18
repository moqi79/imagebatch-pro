"""预设模板与 main 入口测试。"""
from main import load_presets, build_parser


def test_load_presets():
    presets = load_presets()
    assert "xiaohongshu_3x4" in presets
    assert "taobao_1x1" in presets
    assert presets["xiaohongshu_3x4"]["params"]["resize"]["width"] == 1080


def test_load_presets_returns_dict():
    presets = load_presets()
    assert isinstance(presets, dict)
    assert len(presets) >= 4


def test_parser_basic():
    parser = build_parser()
    args = parser.parse_args([
        "--cli", "--input", "./in", "--output", "./out",
        "--compress", "500", "--resize", "1080x1440",
    ])
    assert args.cli is True
    assert args.input == "./in"
    assert args.compress == 500


def test_parser_preset():
    parser = build_parser()
    args = parser.parse_args(["--cli", "--input", "./in", "--preset", "xiaohongshu_3x4"])
    assert args.preset == "xiaohongshu_3x4"


def test_parser_list_presets_flag():
    parser = build_parser()
    args = parser.parse_args(["--list-presets"])
    assert args.list_presets is True
