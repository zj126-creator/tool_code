#!/usr/bin/env python3
"""
models.py — 数据模型定义
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TextRun:
    """一个文本片段（同一段内格式一致的连续文本）"""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False  # 删除线 (del/s 标签)
    font_size: Optional[float] = None  # pt
    color: Optional[str] = None       # hex like #FF0000
    font_name: Optional[str] = None
    href: Optional[str] = None

@dataclass
class Paragraph:
    """一个段落"""
    runs: List[TextRun] = field(default_factory=list)
    alignment: Optional[str] = None   # left/center/right/justify
    bullet: bool = False
    bullet_level: int = 0
    ordered: bool = False  # 有序列表 (ol)
    list_number: int = 0   # 有序列表序号 (1-based)
    space_before: float = 6.0
    space_after: float = 6.0
    line_spacing: Optional[float] = None

@dataclass
class ContentBlock:
    """一个内容块 — 对应 PPTX 中的一个元素"""
    type: str  # title/paragraph/image/table/divider/code_block/spacer
    paragraphs: List[Paragraph] = field(default_factory=list)
    level: int = 0
    image_data: Optional[bytes] = None
    image_ext: Optional[str] = None
    image_alt: str = ""
    table_data: Optional[List[List[List[Paragraph]]]] = None
    table_header: bool = False
    # 合并单元格信息: list of (row, col, rowspan, colspan)
    table_merges: Optional[List] = None
    code_text: str = ""
    bg_color: Optional[str] = None

@dataclass
class SlideContent:
    """一页 slide 的内容"""
    blocks: List[ContentBlock] = field(default_factory=list)
    title: Optional[str] = None
