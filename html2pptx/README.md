# HTML → PPTX 转换器

将 HTML 文件转换为**可编辑的** PowerPoint（.pptx）文件。文本、图片、表格、列表等元素映射为原生 PPTX 元素，非截图，可在 PowerPoint 中直接编辑。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 功能特性

- 📝 **文本完整保留** — 每个字都不丢，加粗、斜体、下划线、删除线等格式不丢失
- 🖼️ **图片嵌入** — 支持本地文件 / HTTP URL / data URI（PNG/JPEG/GIF/WebP/SVG/BMP）
- 📊 **表格转换** — 完整表格结构，支持 colspan/rowspan 合并单元格
- 📋 **列表转换** — ul/ol 嵌套列表，ol 自动编号，支持深层嵌套
- 📐 **自动分页** — 根据内容量自动分配到多页 slide
- 🎨 **样式保留** — 字号、颜色、字体、对齐方式等尽可能保留
- ✏️ **原生可编辑** — 生成的是 PPTX 原生元素（文本框/图片/表格），不是截图

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用

```bash
# 指定输出文件
python src/html2pptx.py input.html output.pptx

# 自动同名输出（input.html → input.pptx）
python src/html2pptx.py input.html

# 演示模式（自动生成测试 HTML 并转换）
python src/html2pptx.py
```

## 📖 支持的 HTML 元素

| 类别 | 元素 | 说明 |
|------|------|------|
| 标题 | h1-h6 | 不同字号标题 |
| 段落 | p | 支持段落内图片提取 |
| 列表 | ul/ol/li | 嵌套列表，ol 自动编号 |
| 图片 | img | 本地/HTTP/data URI |
| 表格 | table/thead/tbody/tr/th/td | 含合并单元格 |
| 代码块 | pre | 等宽字体，深色背景 |
| 引用 | blockquote | 递归处理内部内容 |
| 分隔线 | hr | 矩形线条 |
| 定义列表 | dl/dt/dd | dt 标题 + dd 缩进 |
| 图文组 | figure/figcaption | 图片 + 说明 |
| 内联格式 | strong/b, em/i, u, del/s, a, code, sub, sup, mark | 完整内联样式 |
| 样式属性 | font-size, color, font-family, text-align 等 | CSS 内联样式 |

## 🏗️ 项目结构

```
html2pptx/
├── src/
│   ├── html2pptx.py          # 主入口
│   ├── html_parser.py        # HTML 解析器：DOM → ContentBlock
│   ├── paginator.py          # 分页策略：ContentBlock → SlideContent
│   ├── pptx_builder.py       # PPTX 构建器：SlideContent → .pptx
│   └── models.py             # 数据模型
├── tests/
│   ├── verify.py             # PPTX 内容验证
│   ├── compare.py            # HTML ↔ PPTX 对比
│   ├── scan_bugs.py          # Bug 扫描
│   └── test_edge.py          # 边界测试
├── examples/
│   ├── demo.html             # 演示 HTML
│   ├── demo_output.pptx      # 演示输出
│   ├── adversarial_test.html # 对抗性测试
│   └── adversarial_output.pptx
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| HTML 解析 | BeautifulSoup4 + lxml |
| PPTX 生成 | python-pptx |
| 图片处理 | Pillow |
| 网络请求 | requests |

## 🧪 测试工具

```bash
# PPTX 内容验证
python tests/verify.py output.pptx

# HTML 与 PPTX 内容对比
python tests/compare.py input.html output.pptx

# Bug 扫描
python tests/scan_bugs.py

# 边界测试
python tests/test_edge.py
```

## ⚠️ 已知限制

- HTML 流式布局与 PPTX 固定画布存在本质差异，复杂 CSS 布局无法 100% 还原
- 不支持 JavaScript 动态内容
- 不支持 CSS 动画和过渡效果
- SVG 图片会尝试转换，复杂 SVG 可能不完整

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
