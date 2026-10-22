# -*- coding: utf-8 -*-
"""审计列表页的「详情入口 / 操作列宽度」现状。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

rows = []
for fn in sorted(os.listdir(V)):
    if not fn.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, fn), encoding='utf-8').read()
    if '<el-table' not in s:
        continue
    has_dv = '<DetailView' in s
    # 表格里是否有「详情」按钮（排除详情弹窗标题里的「详情」字样）
    has_detail_btn = bool(re.search(r'>\s*详\s*情\s*<', s))
    has_edit = bool(re.search(r'>\s*编\s*辑\s*<', s))
    op_w = None
    m = re.search(r'label="操作"[^>]*width="(\d+)"', s)
    if m:
        op_w = int(m.group(1))
    btns = len(re.findall(r'<el-button[^>]*link', s))
    rows.append((fn, has_dv, has_detail_btn, has_edit, op_w, btns))

print('%-22s %-8s %-6s %-6s %-6s %s' % ('页面', 'DetailV', '详情', '编辑', '操作宽', 'link按钮数'))
no_detail = []
wide = []
for fn, dv, db, eb, w, b in rows:
    print('%-22s %-8s %-6s %-6s %-6s %d' % (fn, '✓' if dv else '-', '✓' if db else '-',
                                            '✓' if eb else '-', w or '-', b))
    if not db:
        no_detail.append(fn)
    if w and w >= 250:
        wide.append((fn, w))

print('\n缺「详情」入口：%d 个' % len(no_detail))
for fn in no_detail:
    print('   ', fn)
print('\n操作列 ≥250px：%d 个' % len(wide))
for fn, w in wide:
    print('    %-22s %d' % (fn, w))
