"""本地支付确认系统。

工作流程：
1. 用户选择版本（专业版/工作室版），生成支付订单（含机器码、版本、价格、订单号）
2. 用户通过支付宝/微信扫码付款
3. 付款后用户输入「支付凭证码」（由开发者在发卡平台发放，或用户手动联系开发者获取）
4. 本地校验支付凭证码 -> 自动生成授权码 -> 激活

支付凭证码格式：PAY-{订单号后8位}-{版本}-{校验码8位}
校验规则：SHA256(订单号 + 机器码 + 版本 + 价格 + 支付盐值) 截取前8位

两种模式：
- 在线发卡模式：用户从发卡平台购买后获得支付凭证码，本地校验激活
- 离线确认模式：用户付款截图发给开发者，开发者用工具生成确认码，用户输入后激活
"""
import os
import sys
import json
import time
import hashlib
import uuid
from datetime import datetime

from config import PRO, STUDIO, __version__, BASE_DIR

# 支付盐值（与授权码盐值不同，防止交叉破解）
_PAYMENT_SALT = "ImageBatch-Pay-2026-VerifySalt"

# 版本定价
PRICING = {
    PRO: {"name": "专业版", "price": 69.00, "price_text": "¥69"},
    STUDIO: {"name": "工作室版", "price": 299.00, "price_text": "¥299"},
}

# 订单文件
def _resolve_order_dir():
    if getattr(sys, "frozen", False):
        d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                         "ImageBatchPro", "orders")
    else:
        d = os.path.join(BASE_DIR, "orders")
    os.makedirs(d, exist_ok=True)
    return d

ORDER_DIR = _resolve_order_dir()


def _get_machine_id():
    """获取机器码（与 license.py 一致）。"""
    raw = str(uuid.getnode())
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_order(edition):
    """生成支付订单。

    返回订单字典，包含：
    - order_id: 订单号（时间戳+随机数）
    - machine_id: 机器码
    - edition: 版本
    - price: 价格
    - timestamp: 创建时间
    - status: pending
    - confirm_code: 支付确认码（用户付款后输入此码激活）
    """
    if edition not in PRICING:
        raise ValueError(f"无效版本: {edition}，可选: {list(PRICING.keys())}")

    machine_id = _get_machine_id()
    ts = datetime.now()
    order_id = ts.strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:4].upper()

    order = {
        "order_id": order_id,
        "machine_id": machine_id,
        "edition": edition,
        "edition_name": PRICING[edition]["name"],
        "price": PRICING[edition]["price"],
        "price_text": PRICING[edition]["price_text"],
        "timestamp": ts.isoformat(),
        "status": "pending",
    }

    # 生成支付确认码
    order["confirm_code"] = generate_confirm_code(order_id, machine_id, edition,
                                                   PRICING[edition]["price"])
    _save_order(order)
    return order


def generate_confirm_code(order_id, machine_id, edition, price):
    """生成支付确认码。

    格式: PAY-{订单后8位}-{版本缩写}-{校验码8位}
    校验码 = SHA256(订单号 + 机器码 + 版本 + 价格 + 支付盐值)[:8]
    """
    raw = f"{order_id}{machine_id}{edition}{price}{_PAYMENT_SALT}"
    checksum = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()
    edition_short = "P" if edition == PRO else "S"
    order_tail = order_id[-8:]
    return f"PAY-{order_tail}-{edition_short}-{checksum}"


def verify_confirm_code(confirm_code, order_id, machine_id, edition, price):
    """校验支付确认码是否有效。"""
    expected = generate_confirm_code(order_id, machine_id, edition, price)
    return confirm_code.strip().upper() == expected


def confirm_payment(confirm_code, edition=None):
    """用户输入支付确认码后，验证并自动激活。

    流程：
    1. 在本地订单中查找匹配的订单
    2. 校验确认码
    3. 校验通过 -> 生成授权码 -> 激活
    4. 更新订单状态为 confirmed

    返回 (success, message, license_key_or_none)
    """
    confirm_code = confirm_code.strip().upper()
    if not confirm_code.startswith("PAY-"):
        return False, "支付确认码格式错误，应以 PAY- 开头", None

    # 查找匹配的本地订单
    orders = _load_all_orders()
    for order in orders:
        if order.get("status") != "pending":
            continue
        if edition and order.get("edition") != edition:
            continue

        oid = order["order_id"]
        mid = order["machine_id"]
        ed = order["edition"]
        price = order["price"]

        if verify_confirm_code(confirm_code, oid, mid, ed, price):
            # 校验机器码是否匹配当前机器
            current_mid = _get_machine_id()
            if mid != current_mid:
                return False, "订单机器码与当前机器不匹配", None

            # 生成授权码并激活
            from .license import LicenseManager
            key = LicenseManager.generate_key(mid, ed)
            lm = LicenseManager()
            if lm.activate(key, ed):
                # 更新订单状态
                order["status"] = "confirmed"
                order["confirmed_at"] = datetime.now().isoformat()
                order["license_key"] = key
                _save_order(order)
                return True, f"支付确认成功！已激活{PRICING[ed]['name']}。", key
            else:
                return False, "授权码激活失败", None

    return False, "未找到匹配的订单，请确认订单信息或联系开发者", None


def _save_order(order):
    """保存订单到本地文件。"""
    path = os.path.join(ORDER_DIR, f"{order['order_id']}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(order, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _load_all_orders():
    """加载所有本地订单。"""
    orders = []
    if not os.path.isdir(ORDER_DIR):
        return orders
    for fname in os.listdir(ORDER_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(ORDER_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                orders.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return orders


def get_pending_orders():
    """获取所有待支付订单。"""
    return [o for o in _load_all_orders() if o.get("status") == "pending"]


def get_order(order_id):
    """获取指定订单。"""
    path = os.path.join(ORDER_DIR, f"{order_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def format_order_text(order):
    """格式化订单信息为可读文本（供显示/复制）。"""
    lines = [
        f"订单号: {order['order_id']}",
        f"版本: {order['edition_name']}",
        f"价格: {order['price_text']}",
        f"机器码: {order['machine_id']}",
        f"创建时间: {order['timestamp'][:19]}",
        f"状态: {'已确认' if order.get('status') == 'confirmed' else '待支付'}",
    ]
    if order.get("status") == "confirmed":
        lines.append(f"确认时间: {order.get('confirmed_at', '')[:19]}")
    return "\n".join(lines)


def generate_offline_confirm_code(order_id, machine_id, edition, price):
    """开发者工具：为离线订单生成支付确认码。

    当用户通过微信/支付宝转账但未走发卡平台时，
    开发者可用此函数生成确认码发给用户。
    """
    return generate_confirm_code(order_id, machine_id, edition, price)
