# ImageBatch Pro v1.0.0 发行说明

## 发行包内容

| 文件 | 说明 | 分发对象 |
|------|------|----------|
| `dist/ImageBatch-Pro.exe` | 主程序（14MB，免安装） | 所有用户 |
| `setup.iss` | Inno Setup 安装包配置 | 开发者（制作安装包） |
| `assets/presets/*.json` | 预设模板（已内嵌于 exe） | — |
| `tools/gen_license.py` | 授权码生成工具 | 开发者 |

## 版本说明

### 社区版（免费）
- 批量压缩（二分查找目标体积）
- 改尺寸（cover/contain/stretch/pad 四种模式）
- 格式转换（JPG/PNG/WebP/BMP/TIFF）
- 文字水印（9 种位置 + 平铺 + 随机）
- 命令行模式
- 多线程加速

### 专业版（¥69）
- 社区版全部功能
- 图片水印（Logo 叠加）
- EXIF 编辑（读取/清除/写入）
- 预设模板管理
- 处理报告导出（CSV）
- 暗色主题

### 工作室版（¥299）
- 专业版全部功能
- 插件系统
- 批量重命名
- 云同步配置

## 用户激活流程

```bash
# 1. 查看机器码
ImageBatch-Pro.exe --machine-id
# 输出：本机机器码: a2e9db9f10442603

# 2. 将机器码发给开发者

# 3. 开发者生成授权码
python tools/gen_license.py a2e9db9f10442603 pro

# 4. 用户激活
ImageBatch-Pro.exe --activate 3978-3C71-9CEA-6183 pro

# 5. 查看授权状态
ImageBatch-Pro.exe --license-info
```

## 打包流程（开发者）

### 1. 打包 exe
```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --name ImageBatch-Pro \
    --add-data "assets;assets" \
    --hidden-import PIL._tkinter_finder \
    --exclude-module matplotlib --exclude-module numpy \
    --exclude-module pandas --exclude-module scipy \
    main.py
```

### 2. 制作安装包（需 Inno Setup 6）
```bash
# 安装 Inno Setup: https://jrsoftware.org/isdl.php
# 打开 setup.iss，点击编译
# 输出: release/ImageBatch-Pro-Setup-v1.0.0.exe
```

### 3. 批量生成授权码
```bash
# 准备 CSV 文件（machine_id, edition）
python tools/gen_license.py --batch orders.csv
# 输出: orders_keys.csv
```

## 验证清单

- [x] 69 个单元测试全部通过
- [x] exe 打包成功（14.1MB）
- [x] 命令行处理端到端验证
- [x] 授权码生成/激活/持久化验证
- [x] 社区版功能门控生效
- [x] 专业版功能解锁验证
