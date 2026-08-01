# Photo Tool — 桌面照片处理工具

一个基于 Python + tkinter 的桌面照片处理工具，支持照片大小压缩和标准证件照制作（1寸/2寸，蓝底/白底，含自动去背景）。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ 功能特性

### 📐 照片大小压缩
- 支持 50 KB ~ 1 MB 自定义目标大小
- 分辨率缩放 + JPEG 质量组合二分搜索，精确命中目标
- 避免二次编码，压缩结果不反弹

### 📷 标准证件照制作
- 支持 1寸 / 2寸 两种规格
- 支持蓝底 / 白底 两种背景色
- 300 DPI 标准分辨率
- 自动去背景（四角区域生长算法 + alpha 羽化合成）

### 证件照规格

| 规格 | 尺寸(mm) | 像素 | 背景色 |
|------|---------|------|--------|
| 1寸蓝底 | 25×35 | 295×413 | RGB(67,142,219) |
| 1寸白底 | 25×35 | 295×413 | 白色 |
| 2寸蓝底 | 35×53 | 413×626 | RGB(67,142,219) |
| 2寸白底 | 35×53 | 413×626 | 白色 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖库：Pillow, rembg, onnxruntime

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python src/photo_tool.py
```

> 首次使用证件照功能时，rembg 会自动下载 u2net 模型文件（约 176 MB）。如需离线使用，可将 `u2net.onnx` 放在源码同目录下。
>
> 模型下载地址：https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

## 📖 使用说明

### 照片压缩

1. 点击「选择照片」加载图片
2. 设置目标大小（默认 500 KB）
3. 点击「开始压缩」
4. 压缩后的图片自动保存

### 证件照制作

1. 点击「选择照片」加载人物照片
2. 选择规格：1寸 / 2寸
3. 选择背景：蓝底 / 白底
4. 点击「生成证件照」
5. 预览效果，满意后点击「保存」

## 🏗️ 项目结构

```
photo-tool/
├── src/
│   └── photo_tool.py          # 主程序源码
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| GUI | tkinter + ttk（Python 自带） |
| 图像处理 | Pillow |
| 背景去除 | rembg + onnxruntime (u2net 模型) |
| 线程处理 | threading（后台处理，界面不卡顿） |

## 💡 使用提示

1. 证件照制作时，人物尽量居中，四角可见背景，效果最佳
2. 压缩高分辨率照片时可能需要逐步缩小分辨率
3. 首次运行证件照功能需联网下载模型，之后可离线使用
4. 背景替换对均匀背景效果最好，复杂背景可能有瑕疵

## ⚠️ 已知限制

- 背景替换依赖四角区域生长算法，人物碰到图片四角时可能泄漏
- 人像裁切为中心裁切，未做人脸检测
- 复杂/渐变背景的替换效果可能不理想

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
