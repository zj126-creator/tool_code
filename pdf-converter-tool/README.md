# PDF Converter Tool — PDF 万能转换工具

一个基于 Python + tkinter 的桌面 PDF 万能转换工具，支持 PDF 转 Word、转图片、合并、拆分、图片转 PDF、加密解密等六大功能。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📄 **PDF 转 Word** | 提取 PDF 文字生成 .docx 文件，按页分节 |
| 🖼️ **PDF 转图片** | 支持 PNG/JPG 输出，可选 150/200/300 DPI |
| 🔗 **PDF 合并** | 多个 PDF 按选择顺序合并为一个文件 |
| ✂️ **PDF 拆分** | 按指定页数拆分为多个 PDF |
| 📸 **图片转 PDF** | 支持 PNG/JPG/BMP/GIF/TIFF 批量转 PDF |
| 🔒 **PDF 加密** | AES-256 加密，设置打开密码 |
| 🔓 **PDF 解密** | 输入密码移除加密保护 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖库：PyMuPDF, python-docx, Pillow

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python src/pdf_tool.py
```

## 📖 使用说明

### 操作流程

1. 打开程序后，顶部有六个功能选项卡
2. 选择需要的功能选项卡
3. 点击「选择文件」按钮添加文件
4. 设置输出选项（DPI、页数、密码等）
5. 点击「开始转换」按钮
6. 转换完成后文件输出到原文件所在目录的 `Converted` 子文件夹

### 功能详解

#### PDF 转 Word
- 提取 PDF 中的文字内容
- 按页分节生成 .docx 文件
- 保留段落结构

#### PDF 转图片
- 支持 PNG 和 JPG 两种输出格式
- 可选 150 / 200 / 300 DPI 分辨率
- 每页生成一张图片

#### PDF 合并
- 支持添加多个 PDF 文件
- 可调整文件顺序
- 合并输出为一个 PDF

#### PDF 拆分
- 按指定页数拆分
- 例如 10 页 PDF，每 3 页拆分 → 4 个文件（3+3+3+1）

#### 图片转 PDF
- 支持 PNG / JPG / BMP / GIF / TIFF
- 批量添加，按顺序合入 PDF
- 每张图片一页

#### PDF 加密 / 解密
- 加密：AES-256 算法，设置打开密码
- 解密：输入正确密码后移除加密

## 🏗️ 项目结构

```
pdf-converter-tool/
├── src/
│   └── pdf_tool.py          # 主程序源码
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| GUI | tkinter + ttk（Python 自带） |
| PDF 核心 | PyMuPDF (fitz) |
| Word 生成 | python-docx |
| 图片处理 | Pillow |
| 线程处理 | threading（后台转换，界面不卡顿） |

## 💡 使用提示

1. 转换过程中界面不会卡死（后台线程执行）
2. 输出文件默认保存在原文件目录的 `Converted` 文件夹下
3. PDF 转图片的 DPI 越高，图片越清晰但文件越大
4. 加密后的 PDF 需要密码才能打开，请妥善保管密码

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
