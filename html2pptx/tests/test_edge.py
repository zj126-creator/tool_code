#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from html_parser import HTMLParser
from paginator import SlidePaginator
from pptx_builder import PPTXBuilder

tests = [
    ("empty", "<html><body></body></html>"),
    ("text_only", "<html><body>纯文本</body></html>"),
    ("no_body", "<div>无body标签</div>"),
    ("only_br", "<body><br><br><br></body>"),
    ("nested_div", "<body><div><div><div>深层嵌套</div></div></div></body>"),
    ("special_chars", "<body>&amp;&lt;&gt;&nbsp;&copy;&reg;&trade;</body>"),
]

for name, html in tests:
    print(f"=== {name} ===")
    p = HTMLParser()
    blocks = p.parse(html)
    print(f"  blocks: {len(blocks)}")
    for i, b in enumerate(blocks):
        txt = ""
        for para in b.paragraphs:
            for r in para.runs:
                txt += r.text
        if b.type == 'code_block':
            txt = b.code_text
        print(f"  blk{i}: type={b.type} txt={txt[:50]!r}")

    pag = SlidePaginator()
    slides = pag.paginate(blocks)
    print(f"  slides: {len(slides)}")

    outpath = f"test_{name}.pptx"
    b = PPTXBuilder()
    b.build(slides, outpath)
    print(f"  file: {outpath} ({os.path.getsize(outpath)} bytes)")
    print()

print("ALL EDGE CASES PASSED")
