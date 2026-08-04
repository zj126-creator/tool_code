#!/usr/bin/env python3
"""
html2pptx.py — 主入口
HTML → 可编辑 PPTX 转换器

用法:
  python html2pptx.py input.html output.pptx
  python html2pptx.py input.html              # → output.pptx
  python html2pptx.py                         # 交互式

从第一性原理出发的设计:
1. HTML 是结构化文档 → 解析 DOM 树提取每个内容块
2. PPTX 是固定画布 → 每个内容块映射为原生元素（文本框/图片/表格）
3. "一模一样" = 文本内容不丢失 + 格式尽可能保留 + 元素可编辑
4. 自动分页: 按内容量将块分配到多页 slide
"""
import sys
import os

# 确保能找到同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from html_parser import HTMLParser
from paginator import SlidePaginator
from pptx_builder import PPTXBuilder


def convert(html_path: str, pptx_path: str, slide_width: float = 10.0, slide_height: float = 7.5):
    """
    将 HTML 文件转换为可编辑的 PPTX 文件

    Args:
        html_path: HTML 文件路径或 HTML 字符串
        pptx_path: 输出 PPTX 文件路径
        slide_width: 幻灯片宽度（英寸），默认 10.0（16:9）
        slide_height: 幻灯片高度（英寸），默认 7.5（16:9）
    """
    print(f"[1/4] 解析 HTML: {html_path}")
    parser = HTMLParser()
    blocks = parser.parse(html_path)
    print(f"    → 提取到 {len(blocks)} 个内容块")

    # 统计
    block_types = {}
    for b in blocks:
        block_types[b.type] = block_types.get(b.type, 0) + 1
    print(f"    → 类型分布: {block_types}")

    print(f"[2/4] 分页中...")
    paginator = SlidePaginator(slide_width, slide_height)
    slides = paginator.paginate(blocks)
    print(f"    → 生成 {len(slides)} 页幻灯片")

    print(f"[3/4] 构建 PPTX: {pptx_path}")
    builder = PPTXBuilder(slide_width, slide_height)
    builder.build(slides, pptx_path)

    print(f"[4/4] 完成!")
    print(f"    输出文件: {pptx_path}")
    print(f"    文件大小: {os.path.getsize(pptx_path) / 1024:.1f} KB")


def main():
    if len(sys.argv) >= 3:
        html_path = sys.argv[1]
        pptx_path = sys.argv[2]
    elif len(sys.argv) == 2:
        html_path = sys.argv[1]
        base = os.path.splitext(html_path)[0]
        pptx_path = base + '.pptx'
    else:
        print("用法: python html2pptx.py <input.html> [output.pptx]")
        print("      不指定 output 则同名 .pptx")
        # 演示模式
        print("\n运行演示: 生成测试 HTML 并转换...")
        demo_html = os.path.join(os.path.dirname(__file__), 'demo.html')
        generate_demo_html(demo_html)
        html_path = demo_html
        pptx_path = os.path.join(os.path.dirname(__file__), 'demo_output.pptx')

    if not os.path.isfile(html_path):
        print(f"错误: 文件不存在: {html_path}")
        sys.exit(1)

    convert(html_path, pptx_path)


def generate_demo_html(path):
    """生成演示 HTML"""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>演示文档</title>
</head>
<body>

<h1>HTML 转 PPTX 演示</h1>

<p>这是一个从第一性原理出发开发的 HTML→PPTX 转换器。它能将 HTML 内容<strong>一字不差</strong>地转换为<em>可编辑</em>的 PowerPoint 文件。</p>

<h2>核心特性</h2>

<ul>
  <li>文本内容完整保留，<strong>加粗</strong>、<em>斜体</em>、<u>下划线</u>等格式不丢失</li>
  <li>字体大小、颜色等样式尽可能保留</li>
  <li>图片自动嵌入（支持本地/HTTP/data URI）</li>
  <li>表格结构完整保留
    <ul>
      <li>表头特殊样式</li>
      <li>交替行颜色</li>
    </ul>
  </li>
  <li>列表层级正确映射</li>
</ul>

<h2>表格示例</h2>

<table border="1">
  <thead>
    <tr>
      <th>功能</th>
      <th>支持</th>
      <th>说明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>文本</td>
      <td>✓</td>
      <td>所有文本内容</td>
    </tr>
    <tr>
      <td>图片</td>
      <td>✓</td>
      <td>PNG/JPEG/GIF/WebP</td>
    </tr>
    <tr>
      <td>表格</td>
      <td>✓</td>
      <td>完整表格结构</td>
    </tr>
  </tbody>
</table>

<h2>代码块</h2>

<pre>
def hello():
    print("Hello, World!")
</pre>

<h2>段落对齐</h2>

<p style="text-align: center;">这段文字居中对齐</p>
<p style="text-align: right;">这段文字右对齐</p>
<p style="color: #FF0000; font-size: 20px;">这段文字红色且大号</p>

<h3>第三级标题</h3>

<p>程序会根据内容量自动分页，确保每页内容不过载。所有生成的 PPTX 元素都是<strong>原生可编辑</strong>的，不是截图。</p>

<hr>

<p>感谢使用!</p>

</body>
</html>'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"    生成演示 HTML: {path}")


if __name__ == '__main__':
    main()
