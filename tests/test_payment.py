"""支付系统测试。"""
import os
import json

from core.payment import (
    generate_order, confirm_payment, generate_confirm_code,
    verify_confirm_code, generate_offline_confirm_code,
    PRICING, _get_machine_id, _resolve_order_dir, format_order_text,
)
from core.license import LicenseManager, get_license_manager
from config import PRO, STUDIO


def _fresh_env(tmp_path, monkeypatch):
    """创建使用临时目录的测试环境。"""
    order_dir = tmp_path / "orders"
    order_dir.mkdir(exist_ok=True)
    monkeypatch.setattr("core.payment.ORDER_DIR", str(order_dir))

    lic_file = tmp_path / "license.dat"
    monkeypatch.setattr("core.license.LICENSE_FILE", str(lic_file))
    monkeypatch.setattr(LicenseManager, "_get_machine_id",
                        staticmethod(lambda: "test_machine_001"))
    monkeypatch.setattr("core.payment._get_machine_id",
                        lambda: "test_machine_001")
    # 重置全局单例
    import core.license
    core.license._license_manager = None


def test_pricing():
    assert PRICING[PRO]["price"] == 69.00
    assert PRICING[STUDIO]["price"] == 299.00
    assert "¥69" in PRICING[PRO]["price_text"]
    assert "¥299" in PRICING[STUDIO]["price_text"]


def test_generate_order(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    assert order["edition"] == PRO
    assert order["price"] == 69.00
    assert order["machine_id"] == "test_machine_001"
    assert order["status"] == "pending"
    assert order["confirm_code"].startswith("PAY-")
    assert len(order["order_id"]) > 10


def test_confirm_code_format(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(STUDIO)
    code = order["confirm_code"]
    parts = code.split("-")
    assert len(parts) == 4
    assert parts[0] == "PAY"
    assert parts[2] == "S"  # studio


def test_verify_correct_confirm_code(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    result = verify_confirm_code(
        order["confirm_code"],
        order["order_id"],
        order["machine_id"],
        PRO,
        order["price"],
    )
    assert result is True


def test_verify_wrong_confirm_code(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    result = verify_confirm_code(
        "PAY-WRONGCODE-P-00000000",
        order["order_id"],
        order["machine_id"],
        PRO,
        order["price"],
    )
    assert result is False


def test_confirm_payment_success(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    success, message, key = confirm_payment(order["confirm_code"])
    assert success is True
    assert "专业版" in message
    assert key is not None

    # 验证授权已激活
    lm = get_license_manager()
    assert lm.edition == PRO
    assert lm.is_activated


def test_confirm_payment_wrong_code(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    generate_order(PRO)
    success, message, key = confirm_payment("PAY-00000000-P-00000000")
    assert success is False
    assert key is None


def test_confirm_payment_wrong_machine(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    # 切换到另一台机器
    monkeypatch.setattr(LicenseManager, "_get_machine_id",
                        staticmethod(lambda: "different_machine"))
    monkeypatch.setattr("core.payment._get_machine_id",
                        lambda: "different_machine")
    success, message, _ = confirm_payment(order["confirm_code"])
    assert success is False
    assert "机器码" in message


def test_confirm_payment_no_pending(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    success, message, _ = confirm_payment("PAY-XXXXXXXX-P-XXXXXXXX")
    assert success is False


def test_order_persisted(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    order_file = tmp_path / "orders" / f"{order['order_id']}.json"
    assert order_file.exists()
    data = json.loads(order_file.read_text())
    assert data["order_id"] == order["order_id"]


def test_order_status_after_confirm(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(STUDIO)
    confirm_payment(order["confirm_code"])

    from core.payment import get_order
    updated = get_order(order["order_id"])
    assert updated["status"] == "confirmed"
    assert "confirmed_at" in updated
    assert "license_key" in updated


def test_offline_confirm_code():
    """开发者用 --pay 参数生成离线确认码。"""
    code = generate_offline_confirm_code(
        "20260818143000ABCD", "test_machine_001", PRO, 69.00
    )
    assert code.startswith("PAY-")
    parts = code.split("-")
    assert parts[2] == "P"

    # 验证与正常生成的确认码一致
    code2 = generate_confirm_code(
        "20260818143000ABCD", "test_machine_001", PRO, 69.00
    )
    assert code == code2


def test_format_order_text(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(PRO)
    text = format_order_text(order)
    assert order["order_id"] in text
    assert "专业版" in text
    assert "¥69" in text
    assert "待支付" in text


def test_studio_activation(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    order = generate_order(STUDIO)
    success, message, _ = confirm_payment(order["confirm_code"])
    assert success is True
    lm = get_license_manager()
    assert lm.edition == STUDIO
    assert lm.is_feature_unlocked("plugins")
