#!/usr/bin/env python3
"""
html_parser.py — HTML DOM → ContentBlock 列表

第一性原理: HTML DOM 树中每个叶子节点都包含内容信息。
解析器的职责是遍历 DOM 树，将每个节点的内容完整提取为结构化数据，
不丢失任何文本字符、不改变任何格式语义。
"""
import os
import re
import base64
import urllib.request
from typing import List, Optional

from bs4 import BeautifulSoup, Tag, NavigableString, CData, Comment, Doctype

from models import TextRun, Paragraph, ContentBlock


# PPTX 字号有效范围: 1pt ~ 4000pt (EMU 100~400000)
MIN_FONT_SIZE = 1.0
MAX_FONT_SIZE = 4000.0


class HTMLParser:
    BLOCK_TAGS = {'div','p','h1','h2','h3','h4','h5','h6',
                  'ul','ol','li','table','tr','td','th','thead',
                  'tbody','tfoot','img','hr','blockquote','pre','section',
                  'article','header','footer','main','figure','figcaption','br',
                  'dl','dt','dd'}
    HEADING_TAGS = {'h1','h2','h3','h4','h5','h6'}

    # 命名颜色映射
    NAMED_COLORS = {
        'red':'#FF0000','green':'#008000','blue':'#0000FF','black':'#000000',
        'white':'#FFFFFF','yellow':'#FFFF00','gray':'#808080','grey':'#808080',
        'silver':'#C0C0C0','maroon':'#800000','olive':'#808000','lime':'#00FF00',
        'aqua':'#00FFFF','teal':'#008080','navy':'#000080','fuchsia':'#FF00FF',
        'purple':'#800080','orange':'#FFA500','pink':'#FFC0CB','brown':'#A52A2A',
        'cyan':'#00FFFF','magenta':'#FF00FF','gold':'#FFD700',
        'lightgray':'#D3D3D3','darkgray':'#A9A9A9','lightblue':'#ADD8E6',
        'lightgreen':'#90EE90','lightyellow':'#FFFFE0','darkred':'#8B0000',
        'darkblue':'#00008B','darkgreen':'#006400','indigo':'#4B0082',
        'violet':'#EE82EE','coral':'#FF7F50','crimson':'#DC143C',
        'salmon':'#FA8072','tomato':'#FF6347','khaki':'#F0E68C',
        'lavender':'#E6E6FA','beige':'#F5F5DC','ivory':'#FFFFF0',
    }

    # CSS 颜色关键字 → 不转换，用 None 表示"不设置颜色"
    CSS_COLOR_KEYWORDS = {'transparent','inherit','currentColor','initial','unset','revert'}

    def __init__(self):
        self.soup = None

    def parse(self, html_content: str) -> List[ContentBlock]:
        """解析 HTML 字符串或文件路径，返回内容块列表"""
        if os.path.isfile(html_content):
            with open(html_content, 'r', encoding='utf-8') as f:
                html_content = f.read()
        self.soup = BeautifulSoup(html_content, 'lxml')
        # 清除脚本、样式和注释
        for tag in self.soup.find_all(['script','style','noscript']):
            tag.decompose()
        # 清除 HTML 注释
        for c in self.soup.find_all(string=lambda t: isinstance(t, Comment)):
            c.extract()
        blocks = []
        body = self.soup.find('body') or self.soup
        for child in body.children:
            self._parse_node(child, blocks)
        return blocks

    def _parse_node(self, node, blocks: List[ContentBlock], list_context: dict = None):
        """递归解析 DOM 节点"""
        # 跳过注释和文档类型声明
        if isinstance(node, (Comment, Doctype)):
            return
        if isinstance(node, NavigableString):
            # 纯文本节点（非 Comment/Doctype/CData）
            if isinstance(node, CData):
                # CDATA 内容作为代码文本
                text = str(node)
                if text.strip():
                    blocks.append(ContentBlock(type='code_block', code_text=text))
                return
            text = str(node).strip()
            if text:
                para = self._build_paragraph_from_text_node(node)
                blocks.append(ContentBlock(type='paragraph', paragraphs=[para]))
            return
        if not isinstance(node, Tag):
            return
        tag_name = node.name.lower()

        # 标题 h1-h6
        if tag_name in self.HEADING_TAGS:
            level = int(tag_name[1])
            para = self._build_paragraph_from_tag(node)
            blocks.append(ContentBlock(type='title', paragraphs=[para], level=level))
            return

        # 段落 p
        if tag_name == 'p':
            # 段落内可能包含图片等内联元素，需要特殊处理
            self._parse_paragraph_tag(node, blocks)
            return

        # 列表 ul/ol
        if tag_name in ('ul','ol'):
            self._parse_list(node, blocks, ordered=(tag_name=='ol'), level=0, start=1)
            return

        # 图片 img
        if tag_name == 'img':
            block = self._build_image_block(node)
            if block:
                blocks.append(block)
            return

        # 分隔线 hr
        if tag_name == 'hr':
            blocks.append(ContentBlock(type='divider'))
            return

        # 代码块 pre
        if tag_name == 'pre':
            # 保留原始 HTML 源码（包括 <div> 等标签文本）
            code_text = self._extract_pre_content(node)
            blocks.append(ContentBlock(type='code_block', code_text=code_text))
            return

        # 引用 blockquote
        if tag_name == 'blockquote':
            # 递归处理 blockquote 内的子节点（可能含列表等）
            inner_blocks = []
            for child in node.children:
                self._parse_node(child, inner_blocks)
            # 给所有内部块加背景色
            for ib in inner_blocks:
                ib.bg_color = '#F0F0F0'
            blocks.extend(inner_blocks)
            return

        # 表格 table
        if tag_name == 'table':
            block = self._build_table_block(node)
            if block:
                blocks.append(block)
            return

        # figure
        if tag_name == 'figure':
            img_tag = node.find('img')
            caption_tag = node.find('figcaption')
            if img_tag:
                block = self._build_image_block(img_tag)
                if block and caption_tag:
                    block.image_alt = caption_tag.get_text().strip()
                if block:
                    blocks.append(block)
            return

        # 定义列表 dl
        if tag_name == 'dl':
            self._parse_definition_list(node, blocks)
            return

        # br
        if tag_name == 'br':
            blocks.append(ContentBlock(type='spacer'))
            return

        # 容器标签 — 递归或当段落
        if tag_name in ('div','section','article','header','footer','main','span','a','strong','em','b','i','u','del','s','code','mark'):
            # 检查是否有块级子节点
            has_block_children = any(
                isinstance(c, Tag) and c.name.lower() in self.BLOCK_TAGS
                for c in node.children
            )
            # 检查是否包含 img 子节点
            has_img = node.find('img') is not None

            if not has_block_children and not has_img:
                direct_text = node.get_text(strip=True)
                if direct_text:
                    para = self._build_paragraph_from_tag(node)
                    if para.runs:
                        blocks.append(ContentBlock(type='paragraph', paragraphs=[para]))
                return
            # 有块级子元素或图片 → 递归
            for child in node.children:
                self._parse_node(child, blocks, list_context)
            return

        # 其他 — 递归子节点
        for child in node.children:
            self._parse_node(child, blocks, list_context)

    def _parse_paragraph_tag(self, tag: Tag, blocks: List[ContentBlock]):
        """解析 <p> 标签，处理段落内的图片等内联元素"""
        # 检查是否包含图片
        img_tags = tag.find_all('img')
        if not img_tags:
            # 普通段落
            para = self._build_paragraph_from_tag(tag)
            if para.runs:
                blocks.append(ContentBlock(type='paragraph', paragraphs=[para]))
            return

        # 段落含图片：遍历子节点，图片→image block，文本→paragraph block
        # 先尝试提取所有文本和图片
        text_parts = []
        for child in tag.children:
            if isinstance(child, Tag) and child.name.lower() == 'img':
                img_block = self._build_image_block(child)
                if img_block:
                    blocks.append(img_block)
            elif isinstance(child, Tag) and child.name.lower() == 'br':
                text_parts.append('\n')
            else:
                # 提取文本
                t = child.get_text() if isinstance(child, Tag) else str(child)
                if t.strip():
                    text_parts.append(t.strip())

        if text_parts:
            combined = ' '.join(text_parts)
            if combined.strip():
                para = Paragraph(runs=[TextRun(text=combined)])
                blocks.append(ContentBlock(type='paragraph', paragraphs=[para]))

    def _extract_pre_content(self, pre_tag: Tag) -> str:
        """
        提取 <pre> 标签内的原始内容，包括 HTML 标签的文本形式。

        第一性原理: <pre> 是预格式化文本，其内容应被当作"源代码"逐字保留。
        如果 <pre> 内有 <code> 子标签，提取 <code> 的内容。
        对于 <pre> 内的 HTML 标签（如 <div>），应保留为文本 "<div>" 而非解析为 DOM。
        """
        # 如果有 <code> 子标签，取它的内容
        code_tag = pre_tag.find('code')
        target = code_tag if code_tag else pre_tag

        # 用 decode() 获取内部 HTML 源码（包括标签文本）
        # 这样 <div>text</div> 会保留为 "<div>text</div>"
        result_parts = []
        for child in target.children:
            if isinstance(child, NavigableString) and not isinstance(child, (Comment, Doctype)):
                result_parts.append(str(child))
            elif isinstance(child, Tag):
                # 保留标签的原始 HTML 文本
                result_parts.append(str(child))
            # 跳过注释

        content = ''.join(result_parts)
        # 去掉首尾空行但保留内部换行
        return content.strip('\n')

    def _parse_list(self, tag: Tag, blocks: List[ContentBlock],
                    ordered: bool, level: int, start: int = 1):
        """
        解析列表 (ul/ol)，正确处理嵌套。

        第一性原理: <li> 的直接文本内容是该列表项的内容，
        嵌套的 <ul>/<ol> 是子列表，应递归处理但不能将子列表文本混入父项。
        """
        # ol 的 start 属性
        if ordered:
            start_val = tag.get('start', '1')
            try:
                start = int(start_val)
            except ValueError:
                start = 1

        item_num = start
        for li in tag.find_all('li', recursive=False):
            # 分离直接文本和嵌套列表
            nested_lists = []
            direct_children = []
            for child in li.children:
                if isinstance(child, Tag) and child.name.lower() in ('ul', 'ol'):
                    nested_lists.append(child)
                else:
                    direct_children.append(child)

            # 从直接子节点提取文本（不含嵌套列表内容）
            para = self._build_paragraph_from_children(
                direct_children, bullet=True, bullet_level=level,
                ordered=ordered, list_number=item_num
            )
            if para.runs:
                blocks.append(ContentBlock(type='paragraph', paragraphs=[para]))

            # 递归处理嵌套列表
            for nested in nested_lists:
                nested_name = nested.name.lower()
                self._parse_list(nested, blocks,
                                ordered=(nested_name=='ol'),
                                level=level+1,
                                start=int(nested.get('start', '1')) if nested_name=='ol' else 1)

            item_num += 1

    def _build_paragraph_from_children(self, children, bullet=False,
                                       bullet_level=0, ordered=False, list_number=0) -> Paragraph:
        """从一组子节点构建段落"""
        para = Paragraph(bullet=bullet, bullet_level=bullet_level,
                        ordered=ordered, list_number=list_number)

        # 合并所有直接子节点的文本和样式
        inherited = {}
        for child in children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    run = TextRun(text=text)
                    run.bold = inherited.get('bold', False)
                    run.italic = inherited.get('italic', False)
                    run.underline = inherited.get('underline', False)
                    run.strikethrough = inherited.get('strikethrough', False)
                    run.font_size = inherited.get('font_size')
                    run.color = inherited.get('color')
                    run.font_name = inherited.get('font_name')
                    run.href = inherited.get('href')
                    para.runs.append(run)
            elif isinstance(child, Tag):
                child_name = child.name.lower()
                new_inherited = dict(inherited)
                self._apply_tag_style_to_run(child, new_inherited)

                if child_name in ('strong','b'):
                    new_inherited['bold'] = True
                elif child_name in ('em','i'):
                    new_inherited['italic'] = True
                elif child_name == 'u':
                    new_inherited['underline'] = True
                elif child_name in ('del','s','strike'):
                    new_inherited['strikethrough'] = True
                elif child_name == 'a':
                    new_inherited['href'] = child.get('href', '')

                # 递归提取该子标签的文本
                sub_runs = []
                self._extract_runs(child, sub_runs, new_inherited)
                para.runs.extend(sub_runs)

        return para

    def _parse_definition_list(self, dl_tag: Tag, blocks: List[ContentBlock]):
        """解析定义列表 <dl>/<dt>/<dd>"""
        for child in dl_tag.children:
            if not isinstance(child, Tag):
                continue
            name = child.name.lower()
            if name == 'dt':
                para = self._build_paragraph_from_tag(child)
                # dt 作为标题样式
                blocks.append(ContentBlock(type='title', paragraphs=[para], level=5))
            elif name == 'dd':
                para = self._build_paragraph_from_tag(child)
                # dd 缩进
                blocks.append(ContentBlock(type='paragraph', paragraphs=[para], bg_color='#F9F9F9'))

    def _build_paragraph_from_tag(self, tag: Tag, bullet: bool = False,
                                   bullet_level: int = 0) -> Paragraph:
        """从 HTML 标签构建段落"""
        para = Paragraph(bullet=bullet, bullet_level=bullet_level)
        # 对齐
        align = tag.get('align','').lower() if tag.get('align') else ''
        style = tag.get('style','') if tag.get('style') else ''
        if not align and style:
            m = re.search(r'text-align:\s*(left|center|right|justify)', style, re.I)
            if m:
                align = m.group(1).lower()
        if align:
            para.alignment = align
        # 提取标签自身的样式作为 inherited 传递给 runs
        inherited = {}
        self._apply_tag_style_to_run(tag, inherited)
        # 提取 runs
        self._extract_runs(tag, para.runs, inherited)
        return para

    def _build_paragraph_from_text_node(self, node) -> Paragraph:
        """从纯文本节点构建段落"""
        text = str(node).strip()
        if not text:
            return Paragraph()
        run = TextRun(text=text)
        parent = node.parent
        if parent and parent.name:
            style_dict = {}
            self._apply_tag_style_to_run(parent, style_dict)
            run.bold = style_dict.get('bold', False)
            run.italic = style_dict.get('italic', False)
            run.underline = style_dict.get('underline', False)
            run.strikethrough = style_dict.get('strikethrough', False)
            run.font_size = style_dict.get('font_size')
            run.color = style_dict.get('color')
            run.font_name = style_dict.get('font_name')
        return Paragraph(runs=[run])

    def _extract_runs(self, tag: Tag, runs: List[TextRun], inherited: dict = None):
        """递归提取文本片段，保留格式"""
        if inherited is None:
            inherited = {}
        for child in tag.children:
            if isinstance(child, (Comment, Doctype)):
                continue
            if isinstance(child, NavigableString):
                if isinstance(child, CData):
                    # CDATA 内容作为纯文本
                    text = str(child)
                    if text.strip():
                        run = TextRun(text=text.strip())
                        self._apply_inherited(run, inherited)
                        runs.append(run)
                    continue
                text = str(child)
                # 保留纯空白文本节点（可能是有意义的空格）
                if text.strip():
                    run = TextRun(text=text.strip())
                    self._apply_inherited(run, inherited)
                    runs.append(run)
                continue
            if not isinstance(child, Tag):
                continue
            child_name = child.name.lower()

            # br → 在最后一个 run 后加换行，或创建空 run
            if child_name == 'br':
                if runs:
                    runs[-1].text += '\n'
                else:
                    runs.append(TextRun(text='\n'))
                continue

            new_inherited = dict(inherited)
            self._apply_tag_style_to_run(child, new_inherited)

            if child_name in ('strong','b'):
                new_inherited['bold'] = True
                self._extract_runs(child, runs, new_inherited)
            elif child_name in ('em','i'):
                new_inherited['italic'] = True
                self._extract_runs(child, runs, new_inherited)
            elif child_name == 'u':
                new_inherited['underline'] = True
                self._extract_runs(child, runs, new_inherited)
            elif child_name in ('del','s','strike'):
                new_inherited['strikethrough'] = True
                self._extract_runs(child, runs, new_inherited)
            elif child_name == 'a':
                new_inherited['href'] = child.get('href','')
                self._extract_runs(child, runs, new_inherited)
            elif child_name == 'span':
                self._extract_runs(child, runs, new_inherited)
            elif child_name == 'font':
                color = child.get('color','')
                if color:
                    new_inherited['color'] = self._normalize_color(color)
                size = child.get('size','')
                if size:
                    try:
                        size_map = {1:8,2:10,3:12,4:14,5:18,6:24,7:36}
                        new_inherited['font_size'] = self._clamp_font_size(size_map.get(int(size),12))
                    except (ValueError, KeyError):
                        pass
                self._extract_runs(child, runs, new_inherited)
            elif child_name == 'code':
                text = child.get_text()
                if text:
                    run = TextRun(text=text, font_name='Consolas',
                                font_size=self._clamp_font_size(inherited.get('font_size',11)))
                    self._apply_inherited(run, inherited)
                    runs.append(run)
            elif child_name == 'sub':
                text = child.get_text()
                if text:
                    run = TextRun(text=text)
                    base_sz = inherited.get('font_size')
                    if base_sz:
                        run.font_size = self._clamp_font_size(base_sz * 0.7)
                    self._apply_inherited(run, inherited)
                    runs.append(run)
            elif child_name == 'sup':
                text = child.get_text()
                if text:
                    run = TextRun(text=text)
                    base_sz = inherited.get('font_size')
                    if base_sz:
                        run.font_size = self._clamp_font_size(base_sz * 0.7)
                    self._apply_inherited(run, inherited)
                    runs.append(run)
            elif child_name == 'mark':
                text = child.get_text()
                if text:
                    run = TextRun(text=text)
                    self._apply_inherited(run, inherited)
                    # mark 标签默认黄色背景，但 PPTX 文本 run 无背景色
                    # 保持文本内容不变即可
                    runs.append(run)
            elif child_name == 'img':
                # 内联图片：提取 alt 文本占位（图片单独处理）
                alt = child.get('alt','') or child.get('title','')
                if alt:
                    runs.append(TextRun(text=f'[{alt}]', italic=True))
            else:
                self._extract_runs(child, runs, new_inherited)

    def _apply_inherited(self, run: TextRun, inherited: dict):
        """将 inherited 样式应用到 run"""
        run.bold = inherited.get('bold', False)
        run.italic = inherited.get('italic', False)
        run.underline = inherited.get('underline', False)
        run.strikethrough = inherited.get('strikethrough', False)
        run.font_size = inherited.get('font_size')
        run.color = inherited.get('color')
        run.font_name = inherited.get('font_name')
        run.href = inherited.get('href')

    @staticmethod
    def _clamp_font_size(size: Optional[float]) -> Optional[float]:
        """限制字号在 PPTX 合法范围内 [1pt, 4000pt]"""
        if size is None:
            return None
        size = float(size)
        if size < MIN_FONT_SIZE:
            return MIN_FONT_SIZE
        if size > MAX_FONT_SIZE:
            return MAX_FONT_SIZE
        return size

    def _apply_tag_style_to_run(self, tag: Tag, style_dict: dict):
        """从标签的 style 和属性提取样式"""
        style = tag.get('style','')
        if style:
            # font-size
            m = re.search(r'font-size:\s*([\d.]+)\s*(px|pt|em|rem|%)?', style, re.I)
            if m:
                val = float(m.group(1))
                unit = (m.group(2) or 'pt').lower()
                if unit == 'px':     val = val * 0.75
                elif unit in ('em','rem'): val = val * 12
                elif unit == '%':   val = val * 0.12
                style_dict['font_size'] = self._clamp_font_size(val)
            # color
            m = re.search(r'color:\s*(#[0-9A-Fa-f]{3,8}|rgb\([^)]+\)|rgba\([^)]+\)|[a-z]+)', style, re.I)
            if m:
                normalized = self._normalize_color(m.group(1))
                if normalized:
                    style_dict['color'] = normalized
            # font-family
            m = re.search(r'font-family:\s*([^;]+)', style, re.I)
            if m:
                fam = m.group(1).strip().strip("'\"")
                style_dict['font_name'] = fam.split(',')[0].strip().strip("'\"")
            # font-weight
            m = re.search(r'font-weight:\s*(bold|bolder|normal|lighter|[0-9]+)', style, re.I)
            if m:
                w = m.group(1).lower()
                if w in ('bold','bolder') or (w.isdigit() and int(w) >= 600):
                    style_dict['bold'] = True
                elif w in ('normal','lighter') or (w.isdigit() and int(w) < 400):
                    style_dict['bold'] = False
            # font-style
            m = re.search(r'font-style:\s*(italic|oblique|normal)', style, re.I)
            if m:
                if m.group(1).lower() in ('italic','oblique'):
                    style_dict['italic'] = True
                else:
                    style_dict['italic'] = False
            # text-decoration
            m = re.search(r'text-decoration:\s*([^;]+)', style, re.I)
            if m:
                deco = m.group(1).lower()
                if 'underline' in deco:
                    style_dict['underline'] = True
                if 'line-through' in deco:
                    style_dict['strikethrough'] = True
        # HTML 属性
        color_attr = tag.get('color','')
        if color_attr:
            normalized = self._normalize_color(color_attr)
            if normalized:
                style_dict['color'] = normalized
        face = tag.get('face','')
        if face:
            style_dict['font_name'] = face.split(',')[0].strip()

    def _normalize_color(self, color_str: str) -> Optional[str]:
        """将各种颜色格式统一为 #RRGGBB，无法处理的返回 None"""
        color_str = color_str.strip()

        # CSS 关键字 → 无法映射为具体颜色，返回 None
        if color_str.lower() in self.CSS_COLOR_KEYWORDS:
            return None

        # 命名颜色
        if color_str.lower() in self.NAMED_COLORS:
            return self.NAMED_COLORS[color_str.lower()]

        # #RGB → #RRGGBB
        if re.match(r'^#[0-9A-Fa-f]{3}$', color_str):
            return '#' + ''.join(c*2 for c in color_str[1:]).upper()

        # #RRGGBB
        if re.match(r'^#[0-9A-Fa-f]{6}$', color_str):
            return color_str.upper()

        # #RRGGBBAA → 取 RGB 部分
        if re.match(r'^#[0-9A-Fa-f]{8}$', color_str):
            return color_str[:7].upper()

        # rgb(r,g,b)
        m = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str, re.I)
        if m:
            r,g,b = int(m.group(1)),int(m.group(2)),int(m.group(3))
            return f'#{r:02X}{g:02X}{b:02X}'

        # rgba(r,g,b,a)
        m = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)', color_str, re.I)
        if m:
            r,g,b = int(m.group(1)),int(m.group(2)),int(m.group(3))
            return f'#{r:02X}{g:02X}{b:02X}'

        # 无法识别 → 原样返回（后续构建器会做 fallback）
        return color_str

    def _build_image_block(self, img_tag: Tag) -> Optional[ContentBlock]:
        """构建图片内容块"""
        src = img_tag.get('src','')
        if not src:
            alt = img_tag.get('alt','') or img_tag.get('title','')
            if alt:
                return ContentBlock(type='paragraph', paragraphs=[
                    Paragraph(runs=[TextRun(text=f'[图片: {alt}]', italic=True)])])
            return None
        alt = img_tag.get('alt','') or img_tag.get('title','')

        # data URI
        if src.startswith('data:image/'):
            try:
                header, data = src.split(',',1)
                ext = 'png'
                if 'jpeg' in header or 'jpg' in header: ext = 'jpg'
                elif 'gif' in header: ext = 'gif'
                elif 'webp' in header: ext = 'webp'
                elif 'svg' in header: ext = 'svg'
                elif 'bmp' in header: ext = 'bmp'
                return ContentBlock(type='image', image_data=base64.b64decode(data),
                                    image_ext=ext, image_alt=alt)
            except Exception:
                if alt:
                    return ContentBlock(type='paragraph', paragraphs=[
                        Paragraph(runs=[TextRun(text=f'[图片: {alt}]', italic=True)])])
                return None

        # 本地文件
        if os.path.isfile(src):
            ext = os.path.splitext(src)[1].lstrip('.').lower() or 'png'
            with open(src,'rb') as f:
                img_data = f.read()
            return ContentBlock(type='image', image_data=img_data, image_ext=ext, image_alt=alt)

        # HTTP URL
        if src.startswith(('http://','https://')):
            try:
                req = urllib.request.Request(src, headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    img_data = resp.read()
                    ct = resp.headers.get('Content-Type','')
                    ext = 'png'
                    if 'jpeg' in ct or 'jpg' in ct: ext = 'jpg'
                    elif 'gif' in ct: ext = 'gif'
                    elif 'webp' in ct: ext = 'webp'
                    elif 'svg' in ct: ext = 'svg'
                    elif 'bmp' in ct: ext = 'bmp'
                return ContentBlock(type='image', image_data=img_data, image_ext=ext, image_alt=alt)
            except Exception:
                if alt:
                    return ContentBlock(type='paragraph', paragraphs=[
                        Paragraph(runs=[TextRun(text=f'[图片: {alt}]', italic=True)])])
                return None
        # 无法识别的 src → 用 alt 占位
        if alt:
            return ContentBlock(type='paragraph', paragraphs=[
                Paragraph(runs=[TextRun(text=f'[图片: {alt}]', italic=True)])])
        return None

    def _build_table_block(self, table_tag: Tag) -> Optional[ContentBlock]:
        """构建表格内容块，支持 colspan/rowspan 合并"""
        rows_data = []
        has_header = False
        merges = []  # [(row, col, rowspan, colspan), ...]

        thead = table_tag.find('thead')
        tbody = table_tag.find('tbody')

        # 收集所有行
        all_rows = []

        # 表头行
        if thead:
            for tr in thead.find_all('tr', recursive=False):
                all_rows.append(('header', tr))
            has_header = True

        # 表体行
        target = tbody or table_tag
        for tr in target.find_all('tr', recursive=False if tbody else True):
            if tr.find_parent('thead'):
                continue
            if tr.find_parent('tbody') and tbody and tr.find_parent('tbody') is not tbody:
                continue
            all_rows.append(('body', tr))

        # 解析每行
        for row_kind, tr in all_rows:
            row = []
            cells = tr.find_all(['th','td'], recursive=False)
            if not cells:
                continue
            for cell in cells:
                col_idx = len(row)
                para = self._build_paragraph_from_tag(cell)
                row.append([para] if para.runs else [Paragraph(runs=[TextRun(text='')])])

                # 处理 colspan/rowspan
                colspan = int(cell.get('colspan', '1'))
                rowspan = int(cell.get('rowspan', '1'))
                if colspan > 1 or rowspan > 1:
                    merges.append((len(rows_data), col_idx, rowspan, colspan))
                    # 填充占位空单元格
                    for _ in range(colspan - 1):
                        row.append([Paragraph(runs=[TextRun(text='')])])

            rows_data.append(row)

        if not rows_data:
            return None

        # 补齐每行列数
        max_cols = max(len(r) for r in rows_data)
        for r in rows_data:
            while len(r) < max_cols:
                r.append([Paragraph(runs=[TextRun(text='')])])

        return ContentBlock(type='table', table_data=rows_data,
                          table_header=has_header, table_merges=merges if merges else None)

    def _get_cell_paras(self, cell_tag: Tag) -> List[Paragraph]:
        """从表格单元格提取所有段落（可能有多个 <p>）"""
        paras = []
        p_tags = cell_tag.find_all('p', recursive=False)
        if p_tags:
            for p in p_tags:
                para = self._build_paragraph_from_tag(p)
                if para.runs:
                    paras.append(para)
                else:
                    paras.append(Paragraph(runs=[TextRun(text='')]))
        else:
            para = self._build_paragraph_from_tag(cell_tag)
            if para.runs:
                paras.append(para)
            else:
                paras.append(Paragraph(runs=[TextRun(text='')]))
        return paras
