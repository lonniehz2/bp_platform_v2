# -*- coding: utf-8 -*-
"""UX 静态扫描：操作列按钮过多、裸 ID 输入、超宽操作列。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

rows_btn = []
rows_id = []
rows_width = []

for fn in sorted(os.listdir(V)):
    if not fn.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, fn), encoding='utf-8').read()
    # 操作列宽度
    for m in re.finditer(r'<el-table-column label="操作"[^>]*width="(\d+)"', s):
        w = int(m.group(1))
        if w > 320:
            rows_width.append((fn, w))
    # 操作列按钮数
    for m in re.finditer(r'<el-table-column label="操作".*?</el-table-column>', s, re.S):
        block = m.group(0)
        n = len(re.findall(r'<el-button', block))
        if n >= 5:
            rows_btn.append((fn, n))
    # 裸 ID 输入
    for m in re.finditer(r'<el-input[^>]*v-model="([^"]*[iI]d)"', s):
        name = m.group(1)
        if not re.search(r'([kK]eyword|orgId|spaceId|houseId|personId|contractId|feeItemId|deviceId)', name):
            continue
        # 仅列出未使用选择器的明显裸 ID
        rows_id.append((fn, name))

print('=== 操作列 >320px ===')
for x in rows_width:
    print(' ', x)
print('=== 操作列按钮 >=5 ===')
for x in rows_btn:
    print(' ', x)
print('=== 可能是裸 ID 的输入（需人工确认） ===')
seen = set()
for fn, name in rows_id:
    if (fn, name) in seen:
        continue
    seen.add((fn, name))
    print(' ', fn, name)
