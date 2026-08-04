#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from html_parser import HTMLParser

p = HTMLParser()
blocks = p.parse('adversarial_test.html')

print(f"Total blocks: {len(blocks)}")
print()

# BUG-01: font-size 0/1px
print("=== BUG-01: font-size < 2pt ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        for r in para.runs:
            if r.font_size is not None and r.font_size < 2:
                print(f"  blk={i} sz={r.font_size} txt={r.text[:30]!r}")

# BUG-10: non-hex color
print("\n=== BUG-10: non-hex color ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        for r in para.runs:
            if r.color and not r.color.startswith('#'):
                print(f"  blk={i} color={r.color!r} txt={r.text[:30]!r}")

# BUG-13: pre with HTML tags
print("\n=== BUG-13: pre content ===")
for i, b in enumerate(blocks):
    if b.type == 'code_block':
        print(f"  blk={i} code={b.code_text!r}")

# BUG-19: del/s tags
print("\n=== BUG-19: del/s tags ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        for r in para.runs:
            if r.text and ('删除' in r.text or '另一删除' in r.text):
                print(f"  blk={i} txt={r.text[:30]!r} strike=N/A")

# BUG-22: colspan/rowspan
print("\n=== BUG-22: colspan/rowspan ===")
for i, b in enumerate(blocks):
    if b.type == 'table' and b.table_data:
        print(f"  table blk={i}: {len(b.table_data)} rows x {len(b.table_data[0])} cols, header={b.table_header}")
        for ri, row in enumerate(b.table_data):
            for ci, cell in enumerate(row):
                ts = [r.text for p2 in cell for r in p2.runs if r.text]
                print(f"    [{ri},{ci}] = {ts}")

# BUG-25: dl/dt/dd
print("\n=== BUG-25: dl/dt/dd ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        for r in para.runs:
            if r.text and r.text.strip() in ('术语', '定义内容'):
                print(f"  blk={i} txt={r.text!r}")

# BUG-26: images in paragraph
print("\n=== BUG-26: images in paragraph ===")
for i, b in enumerate(blocks):
    if b.type == 'image':
        print(f"  img blk={i} alt={b.image_alt!r} ext={b.image_ext} data={b.image_data is not None}")
    elif b.type == 'paragraph':
        for para in b.paragraphs:
            for r in para.runs:
                if r.text and '1x1' in r.text:
                    print(f"  img-in-p blk={i} txt={r.text!r}")

# BUG-28: ol ordered list - check if numbered
print("\n=== BUG-28: ol ordered list ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        if para.bullet:
            txt = ''.join(r.text for r in para.runs)[:30]
            print(f"  blk={i} bullet level={para.bullet_level} txt={txt!r}")

# BUG-29: br in _extract_runs - text with \n
print("\n=== BUG-29: br handling ===")
for i, b in enumerate(blocks):
    for para in b.paragraphs:
        for r in para.runs:
            if r.text and '\n' in r.text:
                print(f"  blk={i} txt={r.text!r}")

# BUG-30: empty paragraph p tags
print("\n=== BUG-30: empty paragraphs ===")
for i, b in enumerate(blocks):
    if b.type == 'paragraph':
        total_text = ''.join(r.text for para in b.paragraphs for r in para.runs).strip()
        if not total_text:
            print(f"  blk={i} EMPTY paragraph (still created)")

# BUG-31: blockquote with list
print("\n=== BUG-31: blockquote with list ===")
for i, b in enumerate(blocks):
    if b.bg_color == '#F0F0F0':
        txt = ''.join(r.text for para in b.paragraphs for r in para.runs)[:50]
        print(f"  blk={i} bg={b.bg_color} txt={txt!r}")

print("\n=== SCAN COMPLETE ===")
