# 内置字体

水印功能会优先使用项目内置字体 `NotoSansCJK-Regular.otf`（支持中文），
未找到时自动回退到系统字体：

- Windows：`C:/Windows/Fonts/msyh.ttc`（微软雅黑）
- macOS：`/System/Library/Fonts/PingFang.ttc`（苹方）
- Linux：`/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`（文泉驿正黑）

如需自定义水印字体，将 `.ttf/.otf/.ttc` 文件放入此目录即可。
