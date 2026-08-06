# IM 在线文档表生成器

从日计划导出的 Excel 文件自动生成 IM 在线文档表（Word 格式），基于模板 XML 克隆确保格式完全一致。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 功能特性

- 📊 **Excel 读取** — 自动解析日计划导出的 Excel，提取作业计划、人员、风险等级等信息
- 📝 **Word 生成** — 基于模板 XML 克隆方式，确保输出格式与模板完全一致
- ⚠️ **风险筛选** — 支持按风险等级多选筛选（四级/五级等）
- 👤 **人员信息** — 自动提取工作负责人、同进同出人员、安全检查人员（不含电话号码）
- 📅 **日期自动** — 标题日期和输出文件名自动使用当前日期
- 🖥️ **GUI 界面** — tkinter 图形界面，选择文件、筛选风险等级、一键生成

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python src/im_doc_generator.py
```

### 打包为 exe

```bash
python -m PyInstaller --onefile --windowed --name "IM在线文档表生成器" src/im_doc_generator.py
```

## 📖 使用说明

1. **选择 Excel** — 点击「浏览」选择日计划导出的 Excel 文件（.xlsx）
2. **选择模板** — 选择 Word 模板文件（.docx）
3. **选择输出目录** — 指定生成文件保存位置
4. **筛选风险等级** — 勾选需要包含的风险等级（默认全选）
5. **点击生成** — 自动生成 IM 在线文档表

### Excel 数据说明

Excel 文件需包含以下列（从第 3 行开始）：

| 列索引 | 内容 |
|--------|------|
| A(0) | 作业计划编号 |
| B(1) | 作业计划名称 |
| F(5) | 电压等级 |
| G(6) | 作业类型 |
| I(8) | 作业内容 |
| O(14) | 风险等级 |
| Q(16) | 是否带电作业 |
| AV(47) | 工作负责人姓名 |
| AX(49) | 工作负责人单位 |
| BM(64) | 同进同出人员姓名 |
| BN(65) | 同进同出人员单位 |
| BT(71) | 安全督查人员姓名 |
| BU(72) | 安全督查人员单位 |

> ⚠️ 电话号码列（AW/BO/BV 等）不读取，确保隐私安全。

## 🏗️ 项目结构

```
im-doc-generator/
├── src/
│   └── im_doc_generator.py    # 主程序（含 GUI）
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| GUI | tkinter + ttk |
| Excel 读取 | openpyxl |
| Word 生成 | python-docx（XML 克隆方式） |
| 格式匹配 | deepcopy 模板 `<w:tr>` 元素，只替换文本 |

## 💡 设计原理

### 为什么用 XML 克隆而不是从头创建？

python-docx 从零创建表格时，格式属性（字体、字号、边框、列宽、合并单元格等）需要逐一手动设置，容易遗漏且难以与模板完全一致。

本工具采用**模板 XML 克隆**方式：
1. 读取模板 Word 文件的 XML 结构
2. `deepcopy` 模板中的行元素 `<w:tr>`
3. 只替换 run 中的文本内容，不改变任何格式属性
4. 确保输出与模板格式 100% 一致

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
