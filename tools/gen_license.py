"""授权码生成工具（开发者使用）。

用法：
    # 单个生成
    python tools/gen_license.py <机器码> <版本>

    # 示例
    python tools/gen_license.py abcdef0123456789 pro

    # 批量生成（从 CSV 文件读取机器码）
    python tools/gen_license.py --batch machine_codes.csv

CSV 格式：
    machine_id,edition
    abcdef0123456789,pro
    1234567890abcdef,studio
"""
import sys
import os
import csv

# 确保项目根目录在路径中
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.license import LicenseManager


def generate_one(machine_id, edition):
    """生成单个授权码。"""
    key = LicenseManager.generate_key(machine_id.lower(), edition)
    return key


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    if args[0] == "--batch" and len(args) >= 2:
        csv_path = args[1]
        if not os.path.exists(csv_path):
            print(f"错误：文件不存在 {csv_path}")
            sys.exit(1)

        out_path = os.path.splitext(csv_path)[0] + "_keys.csv"
        count = 0
        with open(csv_path, "r", encoding="utf-8-sig") as f_in:
            reader = csv.DictReader(f_in)
            with open(out_path, "w", newline="", encoding="utf-8-sig") as f_out:
                writer = csv.writer(f_out)
                writer.writerow(["machine_id", "edition", "license_key"])
                for row in reader:
                    mid = row.get("machine_id", "").strip()
                    ed = row.get("edition", "pro").strip()
                    if mid:
                        key = generate_one(mid, ed)
                        writer.writerow([mid, ed, key])
                        count += 1
        print(f"已生成 {count} 个授权码 -> {out_path}")
        return

    if len(args) >= 2:
        machine_id = args[0]
        edition = args[1]
        if edition not in ("pro", "studio"):
            print("错误：版本必须是 pro 或 studio")
            sys.exit(1)
        key = generate_one(machine_id, edition)
        print(f"授权码: {key}")
        print(f"版本: {edition}")
        print(f"机器码: {machine_id}")
        print(f"\n用户激活命令:")
        print(f'  ImageBatch-Pro.exe --activate {key} {edition}')
        return

    print(__doc__)


if __name__ == "__main__":
    main()
