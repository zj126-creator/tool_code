# Batch Rename Tool — 批量重命名工具

一个基于 Python + tkinter 的桌面批量重命名工具，按文件创建时间自动排序命名，支持自定义命名规则、预览和撤销。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ 功能特性

- 📂 **按创建时间自动排序** — 扫描文件夹内所有文件，按创建时间从早到晚排序，自动命名为 1、2、3…
- 🏷️ **自定义命名规则** — 支持设置前缀、后缀、分隔符、起始编号、补零位数
- 🔀 **多种排序方式** — 创建时间 / 修改时间 / 文件名，支持倒序
- 👀 **预览功能** — 执行前预览所有文件的新旧名称对比
- ↩️ **撤销操作** — 一键撤销上次重命名操作
- 🛡️ **安全保护** — 目标重名时自动添加后缀，不会覆盖文件
- 🖥️ **GUI 界面** — 基于 tkinter，操作直观，无需命令行

## 🚀 快速开始

### 方式一：直接运行（需 Python 环境）

```bash
git clone https://github.com/yourusername/toolbox.git
cd toolbox/batch-rename-tool
python src/batch_rename.py
```

> 需要安装 Python 3.8+，tkinter 通常已随 Python 内置安装。

### 方式二：使用预编译 exe（无需 Python）

从 [Releases](../../releases) 页面下载 `批量重命名工具.exe`，双击即可运行。

### 方式三：自行打包为 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "批量重命名工具" src/batch_rename.py
# 生成的 exe 在 dist/ 目录下
```

## 📖 使用说明

### 操作步骤

1. **选择文件夹** — 点击「浏览…」选择包含待重命名文件的文件夹
2. **扫描文件** — 程序自动扫描并按排序方式排列文件
3. **设置命名规则** — 配置前缀、后缀、编号格式等
4. **生成预览** — 查看新旧文件名对比表
5. **执行重命名** — 确认无误后点击执行
6. **撤销**（可选） — 如需恢复，点击「撤销上次操作」

### 命名示例

| 设置 | 结果 |
|------|------|
| 无前缀，起始 1，无补零 | `1.jpg`、`2.jpg`、`3.jpg`… |
| 前缀 `照片`，分隔符 `_`，补零 3 | `照片_001.jpg`、`照片_002.jpg`… |
| 前缀 `IMG`，起始 10，无补零 | `IMG_10.jpg`、`IMG_11.jpg`… |
| 前缀 `2026`，后缀 `vacation`，分隔符 `-` | `2026-1-vacation.jpg`… |

### 注意事项

- 仅处理选定文件夹内的**文件**（不含子目录）
- 建议操作前先备份文件
- 程序不会覆盖已有文件，遇到重名会自动加后缀

## 🏗️ 项目结构

```
batch-rename-tool/
├── src/
│   └── batch_rename.py      # 主程序源码
├── assets/
│   └── 批量重命名工具.exe    # 预编译 exe（可选）
└── README.md
```

## 🔧 技术栈

- **语言**：Python 3.8+
- **GUI 框架**：tkinter（Python 标准库，无需额外安装）
- **打包工具**：PyInstaller
