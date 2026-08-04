#!/usr/bin/env python3
"""
paginator.py — 内容块分页策略

第一性原理: PPTX 每页有固定画布大小。分页器的职责是按内容量
将内容块分配到多页，确保每页内容不过载、不截断。
"""
from typing import List
from models import ContentBlock, SlideContent, Paragraph


class SlidePaginator:
    """将内容块分页到幻灯片"""

    def __init__(self, slide_width_in: float = 10.0, slide_height_in: float = 7.5):
        self.slide_width = slide_width_in
        self.slide_height = slide_height_in
        self.margin = 0.5
        self.content_width = slide_width_in - 2 * self.margin
        self.content_height = slide_height_in - 2 * self.margin

    def paginate(self, blocks: List[ContentBlock]) -> List[SlideContent]:
        """将内容块分页为幻灯片列表"""
        slides = []
        current_slide = SlideContent()
        current_height = 0.0

        for block in blocks:
            block_height = self._estimate_block_height(block)

            # h1-h2 标题 → 新页
            if block.type == 'title' and block.level <= 2:
                if current_slide.blocks:
                    slides.append(current_slide)
                current_slide = SlideContent()
                current_height = 0
                current_slide.title = self._get_block_text(block)
                current_slide.blocks.append(block)
                current_height += block_height
                continue

            # 当前页放不下 → 新页
            if current_height + block_height > self.content_height and current_slide.blocks:
                slides.append(current_slide)
                current_slide = SlideContent()
                current_height = 0

            current_slide.blocks.append(block)
            current_height += block_height

        if current_slide.blocks:
            slides.append(current_slide)

        return slides

    def _get_block_text(self, block: ContentBlock) -> str:
        """提取块的文本"""
        texts = []
        for para in block.paragraphs:
            for run in para.runs:
                texts.append(run.text)
        return ' '.join(texts)[:100]

    def _estimate_block_height(self, block: ContentBlock) -> float:
        """估算块在 slide 上占用的高度（英寸）"""
        if block.type == 'spacer':
            return 0.15
        if block.type == 'divider':
            return 0.2
        if block.type == 'title':
            base = {1: 0.8, 2: 0.7, 3: 0.6, 4: 0.5, 5: 0.4, 6: 0.35}
            return base.get(block.level, 0.5)
        if block.type == 'code_block':
            lines = block.code_text.count('\n') + 1
            return max(0.4, lines * 0.2)
        if block.type == 'image':
            return 2.5
        if block.type == 'table':
            if block.table_data:
                # 考虑合并单元格后的实际行数
                rows = len(block.table_data)
                # 多段落单元格增加高度
                for row in block.table_data:
                    max_paras = max(len(cell) for cell in row) if row else 1
                    if max_paras > 1:
                        rows += (max_paras - 1) * 0.15
                return rows * 0.35
            return 1.0
        if block.type == 'paragraph':
            total_text = ''
            for para in block.paragraphs:
                for run in para.runs:
                    total_text += run.text
                total_text += '\n'
            text_len = len(total_text.strip())
            if text_len == 0:
                return 0.2
            font_size = 14.0
            for para in block.paragraphs:
                for run in para.runs:
                    if run.font_size:
                        font_size = max(1.0, run.font_size)
                        break
                if para.runs and para.runs[0].font_size:
                    font_size = max(1.0, para.runs[0].font_size)
                    break
            line_height_in = (font_size / 72.0) * 1.5
            chars_per_line = max(20, int(self.content_width * 72 / font_size * 1.8))
            # 处理文本中的换行符
            num_lines = 0
            for line in total_text.strip().split('\n'):
                if not line:
                    num_lines += 1
                else:
                    num_lines += max(1, (len(line) + chars_per_line - 1) // chars_per_line)
            extra = 0.1 if any(p.bullet for p in block.paragraphs) else 0
            return num_lines * line_height_in + extra + 0.1
        return 0.3
