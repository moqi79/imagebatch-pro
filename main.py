"""ImageBatch Pro 程序入口。

用法：
    python main.py                              # 启动 GUI（社区版）
    python main.py --edition community          # 强制社区版 tkinter 界面
    python main.py --edition pro                # 启动专业版 PyQt5 界面
    python main.py --cli --input ./in --output ./out --compress 500 --resize 1080x1440
    python main.py --list-presets
"""
import argparse
import json
import os
import sys

# 修复 Windows 控制台 GBK 编码问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import config
from core.utils import setup_logging
from core.processor import ProcessingConfig
from core.batch import BatchProcessor


def load_presets(presets_dir=None):
    """加载所有预设模板，返回 {preset_id: preset_dict}。"""
    presets_dir = presets_dir or config.PRESETS_DIR
    presets = {}
    if not os.path.isdir(presets_dir):
        return presets
    for fname in sorted(os.listdir(presets_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(presets_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pid = data.get("id") or os.path.splitext(fname)[0]
            presets[pid] = data
        except (json.JSONDecodeError, OSError):
            continue
    return presets


def build_config_from_args(args):
    """根据 CLI 参数构建 ProcessingConfig。"""
    cfg = ProcessingConfig()

    if args.compress:
        cfg.compress = {
            "target_size_kb": args.compress,
            "min_quality": args.min_quality or 40,
        }

    if args.resize:
        try:
            w, h = args.resize.lower().split("x")
            cfg.resize = {
                "width": int(w),
                "height": int(h),
                "mode": args.resize_mode or "cover",
                "background": args.background or "#FFFFFF",
                "gravity": args.gravity or "center",
            }
        except ValueError:
            print(f"错误: --resize 格式应为 WxH，收到 {args.resize}")
            sys.exit(2)

    if args.format:
        cfg.convert = {"format": args.format, "quality": args.quality or 85,
                       "keep_alpha": not args.no_alpha}
        cfg.output_format = args.format

    if args.watermark_text:
        cfg.watermark_text = {
            "text": args.watermark_text,
            "position": args.watermark_position or "bottom-right",
            "font_size": args.watermark_size or 36,
            "color": args.watermark_color or "#FFFFFF",
            "opacity": args.watermark_opacity or 0.7,
        }

    if args.watermark_image:
        cfg.watermark_image = {
            "path": args.watermark_image,
            "position": args.watermark_position or "bottom-right",
            "scale": args.watermark_scale or 0.2,
            "opacity": args.watermark_opacity or 0.8,
        }

    if args.clear_exif:
        cfg.exif_action = "clear"

    if args.preset:
        presets = load_presets()
        if args.preset not in presets:
            print(f"错误: 未找到预设 '{args.preset}'，使用 --list-presets 查看可用预设")
            sys.exit(2)
        cfg = ProcessingConfig.from_preset(presets[args.preset])
        # CLI 显式参数覆盖预设
        if args.compress:
            cfg.compress = {"target_size_kb": args.compress,
                            "min_quality": args.min_quality or 40}
        if args.format:
            cfg.convert = {"format": args.format}
            cfg.output_format = args.format
        if args.watermark_text:
            cfg.watermark_text["text"] = args.watermark_text

    cfg.suffix = args.suffix or ""
    return cfg


def run_cli(args):
    """命令行模式。"""
    setup_logging()
    cfg = build_config_from_args(args)

    if not os.path.isdir(args.input):
        print(f"错误: 输入目录不存在: {args.input}")
        sys.exit(2)

    output_dir = args.output or os.path.join(args.input, "output")
    os.makedirs(output_dir, exist_ok=True)

    processor = BatchProcessor(max_workers=args.workers or config.MAX_WORKERS)
    print(f"开始处理：{args.input} -> {output_dir}")
    print(f"操作: {', '.join(_summarize(cfg)) or '无'}")

    results = processor.process(
        args.input,
        output_dir,
        cfg,
        recursive=not args.no_recursive,
        progress_callback=lambda d, t: _print_progress(d, t),
        log_callback=lambda m: print(f"  {m}"),
    )

    _print_report(results, output_dir, args.report)


def _summarize(cfg):
    ops = []
    if cfg.compress:
        ops.append(f"压缩≤{cfg.compress.get('target_size_kb')}KB")
    if cfg.resize:
        ops.append(f"尺寸{cfg.resize.get('width')}x{cfg.resize.get('height')}")
    if cfg.watermark_text.get("text"):
        ops.append("文字水印")
    if cfg.watermark_image.get("path"):
        ops.append("图片水印")
    if cfg.output_format or cfg.convert:
        ops.append(f"格式->{cfg.output_format or cfg.convert.get('format', '')}")
    if cfg.exif_action == "clear":
        ops.append("清除EXIF")
    return ops


def _print_progress(done, total):
    pct = (done / total * 100) if total else 0
    bar_len = 24
    filled = int(bar_len * done / total) if total else 0
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"\r进度: [{bar}] {pct:.0f}% ({done}/{total})")
    sys.stdout.flush()
    if done >= total:
        print()


def _print_report(results, output_dir, report_path):
    """打印处理报告，可选导出 CSV。"""
    success = sum(1 for r in results if r["success"])
    failed = len(results) - success
    total_in = sum(r["input_size"] for r in results)
    total_out = sum(r["output_size"] for r in results if r["success"])
    ratio = (total_out / total_in * 100) if total_in else 0

    print("\n" + "=" * 50)
    print(f"处理完成：成功 {success} / 失败 {failed} / 共 {len(results)} 张")
    print(f"原始体积: {_fmt(total_in)}  输出体积: {_fmt(total_out)}  压缩率: {ratio:.1f}%")
    print("=" * 50)

    if report_path:
        import csv
        with open(report_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["输入文件", "输出文件", "状态", "原始大小", "输出大小", "操作"])
            for r in results:
                w.writerow([
                    os.path.basename(r["input"]),
                    os.path.basename(r["output"]) if r["output"] else "",
                    "成功" if r["success"] else f"失败:{r['error']}",
                    r["input_size"],
                    r["output_size"],
                    " | ".join(r["operations"]),
                ])
        print(f"报告已导出: {report_path}")


def _fmt(num):
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"


def launch_gui(edition):
    """启动图形界面——优先 Web UI（无 tkinter 依赖）。"""
    # Web UI 模式（默认，无额外依赖）
    try:
        from web_server import run_server
        run_server(open_browser=True)
        return
    except Exception as e:
        print(f"Web UI 启动失败: {e}")

    # 回退到 tkinter（如有）
    if edition == config.PRO:
        try:
            from ui.pro.main_window import ProMainWindow
            ProMainWindow().run()
            return
        except ImportError:
            pass

    try:
        from ui.community.main_window import CommunityApp
        CommunityApp().run()
    except ImportError:
        print("无法启动 GUI")
        print("可使用命令行模式：python main.py --cli --input ./in --output ./out")
        sys.exit(1)


def build_parser():
    p = argparse.ArgumentParser(
        prog="imagebatch-pro",
        description="ImageBatch Pro — 图片批量处理助手（压缩/改尺寸/加水印/转格式）",
    )
    p.add_argument("--edition", choices=config.EDITIONS, default=None,
                   help="指定版本（community/pro/studio）")
    p.add_argument("--version", action="version", version=f"ImageBatch Pro {config.__version__}")

    cli = p.add_argument_group("命令行模式")
    cli.add_argument("--cli", action="store_true", help="启用命令行模式")
    cli.add_argument("--input", "-i", help="输入目录")
    cli.add_argument("--output", "-o", help="输出目录")
    cli.add_argument("--compress", type=int, help="目标体积（KB）")
    cli.add_argument("--min-quality", type=int, default=40, help="最低质量（1-95）")
    cli.add_argument("--resize", help="尺寸 WxH，如 1080x1440")
    cli.add_argument("--resize-mode", default="cover",
                     choices=["cover", "contain", "stretch", "pad"], help="裁剪模式")
    cli.add_argument("--background", default="#FFFFFF", help="留白背景色")
    cli.add_argument("--gravity", default="center",
                     choices=["center", "top", "bottom", "left", "right",
                              "top-left", "top-right", "bottom-left", "bottom-right"],
                     help="裁剪重心")
    cli.add_argument("--format", choices=config.WRITE_FORMATS, help="目标格式")
    cli.add_argument("--quality", type=int, default=85, help="输出质量（1-95）")
    cli.add_argument("--no-alpha", action="store_true", help="不保留透明通道")

    wm = p.add_argument_group("水印")
    wm.add_argument("--watermark-text", help="文字水印内容")
    wm.add_argument("--watermark-image", help="图片水印路径（Logo）")
    wm.add_argument("--watermark-position", default="bottom-right",
                    help="水印位置")
    wm.add_argument("--watermark-size", type=int, default=36, help="文字字号")
    wm.add_argument("--watermark-color", default="#FFFFFF", help="文字颜色")
    wm.add_argument("--watermark-opacity", type=float, default=0.7, help="透明度 0-1")
    wm.add_argument("--watermark-scale", type=float, default=0.2, help="图片水印缩放")

    exif = p.add_argument_group("EXIF")
    exif.add_argument("--clear-exif", action="store_true", help="清除 EXIF 元数据")

    pre = p.add_argument_group("预设")
    pre.add_argument("--preset", help="使用预设模板 ID")
    pre.add_argument("--list-presets", action="store_true", help="列出所有可用预设")

    misc = p.add_argument_group("其他")
    misc.add_argument("--workers", type=int, help="并发线程数")
    misc.add_argument("--no-recursive", action="store_true", help="不递归子目录")
    misc.add_argument("--suffix", default="", help="输出文件名后缀")
    misc.add_argument("--report", help="导出 CSV 报告路径")

    lic = p.add_argument_group("授权管理")
    lic.add_argument("--activate", nargs=2, metavar=("KEY", "EDITION"),
                     help="激活授权码（如 --activate ABCD-1234-EF56-7890 pro）")
    lic.add_argument("--license-info", action="store_true", help="查看当前授权状态")
    lic.add_argument("--machine-id", action="store_true", help="显示本机机器码")
    lic.add_argument("--deactivate", action="store_true", help="撤销授权，回到社区版")
    lic.add_argument("--gen-key", nargs=2, metavar=("MACHINE_ID", "EDITION"),
                     help="生成授权码（开发者用，如 --gen-key abcd1234 pro）")

    pay = p.add_argument_group("支付与激活")
    pay.add_argument("--pay", choices=["pro", "studio"], help="生成支付订单")
    pay.add_argument("--confirm-payment", metavar="CODE",
                     help="输入支付确认码激活")
    pay.add_argument("--list-orders", action="store_true", help="查看本地订单")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        presets = load_presets()
        if not presets:
            print("暂无预设模板")
            return
        print(f"可用预设（{len(presets)} 个）:")
        for pid, data in presets.items():
            print(f"  {pid:20s} {data.get('name', '')} — {data.get('description', '')}")
        return

    # ---- 授权管理 ----
    from core.license import get_license_manager, LicenseManager

    if args.machine_id:
        lm = get_license_manager()
        print(f"本机机器码: {lm.machine_id}")
        print("请将此机器码发送给开发者以获取授权码。")
        return

    if args.license_info:
        lm = get_license_manager()
        print(lm.summary())
        feats = lm.get_unlocked_features()
        names = [_feat_name(f) for f in sorted(feats)]
        print(f"已解锁功能: {', '.join(names)}")
        return

    if args.activate:
        key, edition = args.activate
        lm = get_license_manager()
        if lm.activate(key, edition):
            print(f"激活成功！当前版本: {lm.edition}")
            print(lm.summary())
        else:
            print("激活失败：授权码无效或与当前机器不匹配。")
            print(f"请确认机器码为: {lm.machine_id}")
            sys.exit(1)
        return

    if args.deactivate:
        lm = get_license_manager()
        lm.deactivate()
        print("已撤销授权，当前为社区版。")
        return

    if args.gen_key:
        machine_id, edition = args.gen_key
        key = LicenseManager.generate_key(machine_id.lower(), edition)
        print(f"授权码: {key}")
        print(f"版本: {edition} | 机器码: {machine_id}")
        return

    # ---- 支付与激活 ----
    from core.payment import (
        generate_order, confirm_payment, PRICING,
        format_order_text, get_pending_orders, get_order,
        generate_offline_confirm_code,
    )

    if args.pay:
        edition = args.pay
        order = generate_order(edition)
        print("=" * 50)
        print("  支付订单已生成")
        print("=" * 50)
        print(format_order_text(order))
        print("-" * 50)
        print(f"  支付确认码: {order['confirm_code']}")
        print("=" * 50)
        print(f"\n请支付 {order['price_text']} 后，输入确认码激活：")
        print(f'  ImageBatch-Pro.exe --confirm-payment "{order["confirm_code"]}"')
        return

    if args.confirm_payment:
        code = args.confirm_payment
        success, message, key = confirm_payment(code)
        if success:
            print(f"[成功] {message}")
            print(f"授权码: {key}")
            lm = get_license_manager()
            print(lm.summary())
        else:
            print(f"[失败] {message}")
            sys.exit(1)
        return

    if args.list_orders:
        orders = get_pending_orders()
        if not orders:
            print("暂无待支付订单")
            return
        print(f"待支付订单（{len(orders)} 个）:")
        for o in orders:
            print(f"  {o['order_id']} | {o['edition_name']} | {o['price_text']} | {o['timestamp'][:19]}")
            print(f"    确认码: {o.get('confirm_code', 'N/A')}")
        return

    if args.cli:
        if not args.input:
            parser.error("命令行模式需要 --input 参数")
        run_cli(args)
        return

    edition = args.edition or config.detect_edition()
    launch_gui(edition)


def _feat_name(feat):
    from core.license import FEATURE_NAMES
    return FEATURE_NAMES.get(feat, feat)


if __name__ == "__main__":
    main()
