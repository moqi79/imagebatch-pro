"""授权码校验与版本门控系统。

授权码格式：XXXX-XXXX-XXXX-XXXX（16位字母数字）
生成规则：基于机器码 + 版本类型 + 盐值，SHA256 截断后分组。

用法：
    from core.license import LicenseManager
    lm = LicenseManager()
    lm.activate("ABCD-1234-EF56-7890")  # 激活
    lm.is_feature_unlocked("exif")        # 检查功能是否解锁
"""
import os
import sys
import json
import hashlib
import uuid
from datetime import datetime

from config import COMMUNITY, PRO, STUDIO, __version__, BASE_DIR

# 盐值（生产环境应改为随机且保密的值）
_SALT = "ImageBatch-Pro-2026-SecureSalt"

# 各版本解锁的功能列表
FEATURE_MAP = {
    COMMUNITY: {
        "compress", "resize", "convert", "watermark_text", "cli_basic",
    },
    PRO: {
        "compress", "resize", "convert", "watermark_text", "cli_basic",
        "watermark_image", "exif", "presets", "cli_full", "report", "dark_theme",
    },
    STUDIO: {
        "compress", "resize", "convert", "watermark_text", "cli_basic",
        "watermark_image", "exif", "presets", "cli_full", "report", "dark_theme",
        "plugins", "api", "batch_rename", "cloud_sync",
    },
}

# 功能中文名
FEATURE_NAMES = {
    "compress": "批量压缩",
    "resize": "改尺寸",
    "convert": "格式转换",
    "watermark_text": "文字水印",
    "watermark_image": "图片水印",
    "exif": "EXIF 编辑",
    "presets": "预设模板",
    "cli_basic": "基础命令行",
    "cli_full": "完整命令行",
    "report": "处理报告",
    "dark_theme": "暗色主题",
    "plugins": "插件系统",
    "api": "API 接口",
    "batch_rename": "批量重命名",
    "cloud_sync": "云同步",
}

def _resolve_license_file():
    """授权文件路径：优先用户家目录（打包后持久化），开发时用项目目录。"""
    # 打包后 sys.frozen 存在，写到用户 AppData
    if getattr(sys, "frozen", False):
        app_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                               "ImageBatchPro")
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "license.dat")
    return os.path.join(BASE_DIR, "license.dat")


LICENSE_FILE = _resolve_license_file()


class LicenseManager:
    """授权码管理器。"""

    def __init__(self):
        self._edition = COMMUNITY
        self._license_key = None
        self._activated_at = None
        self._machine_id = self._get_machine_id()
        self._load()

    @staticmethod
    def _get_machine_id():
        """获取机器唯一标识。"""
        raw = str(uuid.getnode())
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def generate_key(machine_id, edition):
        """生成授权码（供开发者生成发给用户）。

        参数：
            machine_id: 用户的机器码（16 位）
            edition: "pro" 或 "studio"
        返回：XXXX-XXXX-XXXX-XXXX 格式字符串
        """
        raw = f"{machine_id}-{edition}-{_SALT}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        return "-".join(digest[i:i + 4] for i in range(0, 16, 4))

    def verify(self, key, edition):
        """校验授权码是否匹配本机与版本。"""
        expected = self.generate_key(self._machine_id, edition)
        return key.upper().strip() == expected

    def activate(self, key, edition=PRO):
        """激活授权码。成功返回 True，失败返回 False。"""
        key = key.strip().upper()
        # 尝试指定版本
        if self.verify(key, edition):
            self._edition = edition
            self._license_key = key
            self._activated_at = datetime.now().isoformat()
            self._save()
            return True
        # 自动探测版本
        for ed in (STUDIO, PRO):
            if self.verify(key, ed):
                self._edition = ed
                self._license_key = key
                self._activated_at = datetime.now().isoformat()
                self._save()
                return True
        return False

    def deactivate(self):
        """撤销激活，回到社区版。"""
        self._edition = COMMUNITY
        self._license_key = None
        self._activated_at = None
        if os.path.exists(LICENSE_FILE):
            os.remove(LICENSE_FILE)

    @property
    def edition(self):
        return self._edition

    @property
    def machine_id(self):
        """返回本机机器码（用户需提供此码给开发者换取授权码）。"""
        return self._machine_id

    @property
    def is_activated(self):
        return self._license_key is not None

    def is_feature_unlocked(self, feature):
        """检查某功能是否在当前版本中解锁。"""
        return feature in FEATURE_MAP.get(self._edition, set())

    def get_unlocked_features(self):
        """返回当前版本已解锁的功能集合。"""
        return FEATURE_MAP.get(self._edition, set())

    def _save(self):
        """保存授权信息到本地文件。"""
        data = {
            "edition": self._edition,
            "license_key": self._license_key,
            "activated_at": self._activated_at,
            "machine_id": self._machine_id,
            "version": __version__,
        }
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def _load(self):
        """从本地文件加载授权信息。"""
        if not os.path.exists(LICENSE_FILE):
            return
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            key = data.get("license_key", "")
            edition = data.get("edition", COMMUNITY)
            # 重新校验，防止复制 license.dat 到其他机器
            if key and self.verify(key, edition):
                self._edition = edition
                self._license_key = key
                self._activated_at = data.get("activated_at")
        except (json.JSONDecodeError, OSError):
            pass

    def summary(self):
        """返回授权状态摘要文本。"""
        if not self.is_activated:
            return f"社区版（免费）| 机器码: {self._machine_id}"
        ed_name = {"pro": "专业版", "studio": "工作室版"}.get(self._edition, "社区版")
        date = (self._activated_at or "")[:10]
        return f"{ed_name} | 机器码: {self._machine_id} | 激活日期: {date}"


# 全局单例
_license_manager = None


def get_license_manager():
    """获取全局 LicenseManager 单例。"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
