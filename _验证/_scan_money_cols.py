# -*- coding: utf-8 -*-
"""扫描仍以原始文本展示的金额列。"""
import io
import os
import re

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
KW = ('金额', '租金', '押金', '单价', '应收', '待缴', '已缴', '余额', '补贴', '费用', '实付')

for fn in sorted(os.listdir(V)):
    if not fn.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, fn), encoding='utf-8').read()
    hits = []
    for m in re.finditer(r'<el-table-column([^>]*)/>', s):
        tag = m.group(0)
        label = re.search(r'label="([^"]*)"', tag)
        if not label or not any(k in label.group(1) for k in KW):
            continue
        window = s[m.start():m.start() + 260]
        if '$money' not in window:
            hits.append(label.group(1))
    if hits:
        print(fn, hits)
