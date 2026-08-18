# ImageBatch Pro — 图片批量处理助手

> 一键批量压缩、改尺寸、加水印、转格式。纯本地运行，隐私零泄露。

## 下载安装

### Windows 用户（推荐）

1. 前往 [Releases 页面](https://github.com/moqi79/imagebatch-pro/releases/latest) 下载安装包
2. 双击 `ImageBatch-Pro-Setup-v1.0.0.exe` 运行安装
3. 安装完成后，桌面会出现 **ImageBatch Pro** 快捷方式
4. **双击快捷方式即可打开**，浏览器会自动弹出操作界面

### 免安装版

1. 下载 `ImageBatch-Pro.exe`（14MB）
2. 放到任意目录，双击运行
3. 浏览器自动打开操作界面

### macOS / Linux

```bash
git clone https://github.com/moqi79/imagebatch-pro.git
cd imagebatch-pro
pip install -r requirements.txt
python main.py
```

## 快速开始

### 界面操作（双击打开后）

1. **选择图片目录**：在输入框粘贴图片所在文件夹路径，点击「扫描」
2. **设置处理选项**：
   - 批量压缩：拖动滑块设置目标体积（如 500KB）
   - 改尺寸：输入宽×高，选择裁剪模式
   - 格式转换：选择目标格式（JPG/PNG/WebP）
   - 水印：输入水印文字，选择位置和样式（专业版）
3. 点击 **▶ 开始处理**，等待完成
4. 处理结果在输出目录中（默认在输入目录下的 `output` 文件夹）

### 命令行模式

```bash
# 基础用法：压缩到 500KB + 改尺寸 1080×1080
ImageBatch-Pro.exe --cli --input "C:\图片目录" --output "C:\输出" --compress 500 --resize 1080x1080

# 转换为 WebP 格式
ImageBatch-Pro.exe --cli --input ./photos --format webp

# 加文字水印
ImageBatch-Pro.exe --cli --input ./photos --watermark-text "版权所有"

# 使用预设模板（小红书 3:4）
ImageBatch-Pro.exe --cli --input ./photos --preset xiaohongshu_3x4

# 查看所有预设
ImageBatch-Pro.exe --list-presets
```

## 版本对比

| 功能 | 社区版（免费） | 专业版（¥69） | 工作室版（¥299） |
|------|:---:|:---:|:---:|
| 批量压缩 | ✅ | ✅ | ✅ |
| 改尺寸（4 种模式） | ✅ | ✅ | ✅ |
| 格式转换（5 种格式） | ✅ | ✅ | ✅ |
| 文字水印 | ✅ | ✅ | ✅ |
| 基础命令行 | ✅ | ✅ | ✅ |
| 图片水印（Logo 叠加） | ❌ | ✅ | ✅ |
| EXIF 信息编辑 | ❌ | ✅ | ✅ |
| 预设模板 | ❌ | ✅ | ✅ |
| 处理报告导出 | ❌ | ✅ | ✅ |
| 暗色主题 | ❌ | ✅ | ✅ |
| 插件系统 | ❌ | ❌ | ✅ |
| API 接口 | ❌ | ❌ | ✅ |
| 批量重命名 | ❌ | ❌ | ✅ |
| 云同步配置 | ❌ | ❌ | ✅ |

## 购买与激活

### 在线购买流程

1. 打开软件，点击右上角 **✨ 升级专业版** 按钮
2. 选择版本（专业版 ¥69 / 工作室版 ¥299）
3. 系统生成支付订单（含订单号、机器码、确认码）
4. 扫码或转账付款
5. 输入支付确认码，点击「确认支付并激活」
6. 自动激活，所有付费功能立即解锁

### 命令行购买流程

```bash
# 1. 生成支付订单
ImageBatch-Pro.exe --pay pro

# 2. 付款后输入确认码激活
ImageBatch-Pro.exe --confirm-payment "PAY-XXXXXXXX-P-XXXXXXXX"

# 3. 查看授权状态
ImageBatch-Pro.exe --license-info

# 4. 查看本机机器码
ImageBatch-Pro.exe --machine-id
```

### 离线购买（微信/支付宝转账）

1. 运行 `ImageBatch-Pro.exe --pay pro` 获取订单信息
2. 将订单号和机器码发给开发者
3. 开发者生成确认码发给你
4. 运行 `ImageBatch-Pro.exe --confirm-payment "确认码"` 激活

## 预设模板

| 预设名称 | 尺寸 | 适用平台 |
|----------|------|----------|
| `xiaohongshu_3x4` | 1080×1440 | 小红书 |
| `taobao_1x1` | 800×800 | 淘宝主图 |
| `wechat_cover` | 900×383 | 公众号封面 |
| `instagram_1x1` | 1080×1080 | Instagram |
| `douyin_9x16` | 1080×1920 | 抖音/ TikTok |

```bash
ImageBatch-Pro.exe --list-presets
ImageBatch-Pro.exe --cli --input ./photos --preset xiaohongshu_3x4
```

## 命令行参数大全

```
ImageBatch-Pro.exe [选项]

常用：
  --cli                          启用命令行模式
  --input <目录>                  输入图片目录
  --output <目录>                 输出目录（默认: 输入目录/output）
  --compress <KB>                压缩到指定体积（如 500）
  --resize <WxH>                 改尺寸（如 1080x1080）
  --resize-mode <模式>            cover/contain/stretch/pad
  --format <格式>                jpg/png/webp/bmp/tiff
  --watermark-text <文字>         文字水印内容
  --watermark-position <位置>    水印位置
  --clear-exif                   清除 EXIF 信息
  --preset <名称>                使用预设模板
  --workers <数量>               线程数（默认 4）
  --report <路径>                导出 CSV 报告
  --suffix <后缀>                输出文件名后缀

授权管理：
  --pay <pro|studio>            生成支付订单
  --confirm-payment <确认码>     确认支付并激活
  --activate <授权码> <版本>     直接激活授权码
  --license-info                 查看授权状态
  --machine-id                   显示机器码
  --deactivate                   撤销授权
  --list-orders                  查看待支付订单

其他：
  --list-presets                 列出所有预设
  --version                      显示版本号
```

## 项目结构

```
imagebatch-pro/
├── main.py              # 程序入口（CLI + GUI 启动）
├── web_server.py        # Web UI 服务器（内置 HTTP 服务器）
├── web_ui/              # Web 界面文件
│   ├── index.html       # 主页面
│   ├── style.css        # 样式表
│   └── app.js           # 前端逻辑
├── config.py            # 全局配置
├── core/                # 核心引擎
│   ├── compressor.py    # 批量压缩（二分查找算法）
│   ├── resizer.py       # 改尺寸（4 种模式）
│   ├── watermark.py     # 水印（文字 + 图片）
│   ├── converter.py     # 格式转换
│   ├── processor.py     # 处理流程编排
│   ├── batch.py         # 多线程批量处理
│   ├── license.py       # 授权码系统
│   ├── payment.py       # 支付确认系统
│   └── ...
├── ui/                  # tkinter GUI（备用）
├── plugins/             # 插件系统
├── assets/presets/      # 预设模板
├── tools/               # 开发者工具
├── tests/               # 单元测试（83 个）
├── setup.iss            # Inno Setup 安装包配置
└── requirements.txt     # Python 依赖
```

## 常见问题

### 双击 exe 没反应 / 打不开？

- 安装版：检查是否已安装完成，从桌面快捷方式或开始菜单打开
- 免安装版：等待 2-3 秒，程序正在初始化，浏览器会自动弹出
- 如果浏览器没有自动打开，查看控制台输出的地址，手动在浏览器输入 `http://127.0.0.1:端口`

### 处理后图片在哪里？

默认在输入目录下的 `output` 文件夹中。也可以用 `--output` 指定输出目录。

### 支持哪些图片格式？

读取：JPG、PNG、WebP、BMP、TIFF、GIF
输出：JPG、PNG、WebP、BMP、TIFF

### 一台授权码能用在多台电脑上吗？

不能。授权码与机器码绑定，一个授权码只能在一台电脑上使用。换电脑需要重新购买或联系开发者转移授权。

### 如何退款？

付款后 7 天内如遇无法激活的问题，联系开发者全额退款。

## 开发者指南

### 本地运行

```bash
git clone https://github.com/moqi79/imagebatch-pro.git
cd imagebatch-pro
pip install -r requirements.txt
python main.py          # 启动 Web UI
python main.py --cli   # 命令行模式
```

### 运行测试

```bash
pip install pytest pytest-cov
python -m pytest tests/ -v --cov=core
```

### 打包

```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --name ImageBatch-Pro \
    --add-data "assets;assets" --add-data "web_ui;web_ui" \
    --hidden-import PIL._tkinter_finder \
    main.py
```

### 生成授权码

```bash
# 直接生成授权码
python tools/gen_license.py <机器码> pro

# 生成支付确认码（离线模式）
python tools/gen_license.py --pay <订单号> <机器码> pro
```

## 开源协议

MIT License — 可自由使用、修改、分发。

## 技术支持

- GitHub Issues: [提交问题](https://github.com/moqi79/imagebatch-pro/issues)
- 仓库地址: https://github.com/moqi79/imagebatch-pro
