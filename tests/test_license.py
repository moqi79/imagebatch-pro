"""授权码系统测试。"""
import os
import shutil

from core.license import LicenseManager, FEATURE_NAMES


def _fresh_manager(tmp_path, monkeypatch):
    """创建一个使用临时 license.dat 的 LicenseManager。"""
    lic_file = tmp_path / "license.dat"
    monkeypatch.setattr("core.license.LICENSE_FILE", str(lic_file))
    monkeypatch.setattr(LicenseManager, "_get_machine_id",
                        staticmethod(lambda: "abcdef0123456789"))
    return LicenseManager()


def test_machine_id_format(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    mid = lm.machine_id
    assert len(mid) == 16


def test_community_default(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    assert lm.edition == "community"
    assert not lm.is_activated
    assert lm.is_feature_unlocked("compress")
    assert not lm.is_feature_unlocked("exif")


def test_generate_and_activate_pro(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    key = LicenseManager.generate_key(lm.machine_id, "pro")
    assert lm.activate(key, "pro")
    assert lm.edition == "pro"
    assert lm.is_activated
    assert lm.is_feature_unlocked("exif")
    assert lm.is_feature_unlocked("watermark_image")
    assert not lm.is_feature_unlocked("plugins")


def test_activate_studio(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    key = LicenseManager.generate_key(lm.machine_id, "studio")
    assert lm.activate(key, "studio")
    assert lm.edition == "studio"
    assert lm.is_feature_unlocked("plugins")
    assert lm.is_feature_unlocked("api")


def test_wrong_key_fails(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    assert not lm.activate("XXXX-YYYY-ZZZZ-0000", "pro")
    assert lm.edition == "community"


def test_wrong_machine_fails(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    other_key = LicenseManager.generate_key("other_machine_id", "pro")
    assert not lm.activate(other_key, "pro")


def test_auto_detect_edition(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    key = LicenseManager.generate_key(lm.machine_id, "studio")
    assert lm.activate(key)  # 不指定 edition，自动探测
    assert lm.edition == "studio"


def test_persist_and_reload(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    key = LicenseManager.generate_key(lm.machine_id, "pro")
    assert lm.activate(key, "pro")

    lm2 = _fresh_manager(tmp_path, monkeypatch)
    assert lm2.edition == "pro"
    assert lm2.is_activated


def test_deactivate(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    key = LicenseManager.generate_key(lm.machine_id, "pro")
    lm.activate(key, "pro")
    lm.deactivate()
    assert lm.edition == "community"
    assert not lm.is_activated


def test_summary_text(tmp_path, monkeypatch):
    lm = _fresh_manager(tmp_path, monkeypatch)
    s = lm.summary()
    assert "社区版" in s
    assert "机器码" in s

    key = LicenseManager.generate_key(lm.machine_id, "pro")
    lm.activate(key, "pro")
    s = lm.summary()
    assert "专业版" in s


def test_feature_names_complete():
    for feat in ["compress", "resize", "exif", "plugins", "watermark_image"]:
        assert feat in FEATURE_NAMES
