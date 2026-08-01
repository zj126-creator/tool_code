# Screenshot OCR Tool — 截图OCR工具

桌面截图OCR工具，支持截图识别文字、表格、数学公式，并可导出为 Excel/CSV/Markdown，支持翻译。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ 功能特性

- 📷 **截图识别** — 全局热键 `Ctrl + Alt + A` 一键截图，选区后自动识别
- 📝 **文字识别** — 通用印刷体识别，支持中英文
- 📊 **表格识别** — 高精度表格识别，自动解析为可编辑表格
- 🔢 **公式识别** — 数学公式识别，输出 LaTeX 格式
- 🌐 **翻译功能** — 识别结果翻译为英语/日语/韩语等
- 📤 **多格式导出** — Excel / CSV / Markdown
- 📋 **复制到剪贴板** — 表格复制为 TSV 格式，可直接粘贴到 Excel
- 🖥️ **系统托盘** — 关闭窗口不退出，最小化到托盘

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖库：PyQt5, mss, keyboard, openpyxl, requests

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置腾讯云 API

1. 访问 [腾讯云 API 密钥管理](https://console.cloud.tencent.com/cam/capi)
2. 创建或查看你的 **SecretId** 和 **SecretKey**
3. 确保已开通以下服务：
   - 通用印刷体识别（OCR）
   - 表格识别（OCR）
   - 数学公式识别（OCR）
   - 机器翻译（TMT）
4. 启动应用后点击「⚙ 设置」按钮，填入 SecretId 和 SecretKey

### 运行

```bash
python src/main.py
```

> ⚠️ 全局热键需要管理员权限，建议以管理员身份运行。

## 📖 使用说明

### 截图识别流程

1. 按下 `Ctrl + Alt + A`（或点击「🖼 截图识别」按钮）
2. 拖动鼠标选择屏幕区域
3. 松开鼠标完成截图
4. 选择识别类型：文字 / 表格 / 公式
5. 识别结果显示在对应 Tab 页
6. 导出或复制结果

### 识别类型

| 按钮 | 功能 | API |
|------|------|-----|
| 📝 识别文字 | 通用印刷体识别（中英文） | GeneralBasicOCR |
| 📊 识别表格 | 表格识别（高精度） | RecognizeTableAccurateOCR |
| 🔢 识别公式 | 数学公式识别（LaTeX输出） | FormulaOCR |

### 导出格式

| 格式 | 说明 |
|------|------|
| Excel (.xlsx) | 表格直接转为Excel，文字每行一格 |
| CSV | UTF-8 BOM编码，Windows Excel直接打开不乱码 |
| Markdown | 表格转Markdown表格，文字转纯文本 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl + Alt + A | 全局截图热键 |
| Esc | 取消截图选区 |
| 双击托盘图标 | 恢复主窗口 |

## 🏗️ 项目结构

```
screenshot-ocr-tool/
├── src/
│   └── main.py              # 主程序源码
├── assets/
│   ├── ui_preview.png       # 界面预览
│   └── ui_preview2.png      # 界面预览
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| GUI | PyQt5 |
| 截图 | mss + 自绘选区覆盖层 |
| OCR | 腾讯云 OCR API (v3签名) |
| 表格识别 | 腾讯云 RecognizeTableAccurateOCR |
| 公式识别 | 腾讯云 FormulaOCR |
| 翻译 | 腾讯云 TextTranslate |
| 导出Excel | openpyxl |
| 导出CSV | Python csv (UTF-8 BOM) |
| 全局热键 | keyboard 库 |

## 🔒 安全说明

- API 密钥存储在本地 `config.json`，**不会上传任何服务器**
- `config.json` 已在 `.gitignore` 中排除，不会提交到 Git
- 截图临时文件在下次截图时自动覆盖
- 所有 API 调用通过 HTTPS 加密传输

## 🐛 常见问题

**Q: 提示"识别失败"？**
A: 检查 config.json 中的 SecretId/SecretKey 是否正确，确认已开通对应 OCR 服务。

**Q: 快捷键不生效？**
A: 以管理员身份运行（keyboard 库需要管理员权限注册全局热键）。

**Q: 表格识别不准确？**
A: 确保截图清晰、表格线完整，避免倾斜或模糊。

**Q: 导出的 CSV 在 Excel 中乱码？**
A: 本工具已自动添加 UTF-8 BOM，如仍乱码请检查 Excel 版本。
