# -*- coding: utf-8 -*-
"""对指定页面按按钮数自动加宽操作列（保证单行）。"""
import io
import os
import re
import sys

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')
TARGETS = ['Visits.vue', 'Appeals.vue']

for fn in TARGETS:
    p = os.path.join(V, fn)
    if not os.path.exists(p):
        print(fn, '不存在')
        continue
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'(<el-table-column[^>]*label="操作"[^>]*>)', s)
    if not m:
        print(fn, '未找到操作列')
        continue
    head = m.group(1)
    seg_end = s.find('</el-table-column>', m.end())
    seg = s[m.end():seg_end if seg_end > 0 else m.end() + 2000]
    btns = len(re.findall(r'<el-button[^>]*', seg))
    need = min(440, int(round((btns * 64 + 40) / 10.0)) * 10)
    cur = re.search(r'width="(\d+)"', head)
    cur_w = int(cur.group(1)) if cur else 0
    target = max(cur_w, need)
    if cur:
        new_head = head.replace('width="%d"' % cur_w, 'width="%d"' % target, 1)
    else:
        new_head = head.replace('label="操作"', 'label="操作" width="%d"' % target, 1)
    s = s[:m.start()] + new_head + s[m.end():]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%-14s 按钮 %d 个，宽度 %d → %d' % (fn, btns, cur_w, target))
