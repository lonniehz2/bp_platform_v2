# -*- coding: utf-8 -*-
"""给列表页分页器补「每页条数」：按现有绑定推导变量与刷新函数。"""
import io
import os
import re

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
changed, skipped = [], []

for fn in sorted(os.listdir(V)):
    if not fn.endswith('.vue'):
        continue
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if '<el-pagination' not in s or 'page-sizes' in s:
        continue
    start = s.find('<el-pagination')
    i = start
    quote = None
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == '>':
            break
        i += 1
    tag = s[start:i + 1]
    size_m = re.search(r':page-size="([^"]+)"', tag)
    cur_m = re.search(r':current-page="([^"]+)"', tag)
    change_m = re.search(r'@current-change="([^"]+)"', tag, re.S)
    if not (size_m and cur_m and change_m):
        skipped.append((fn, 'missing bindings'))
        continue
    size_expr, cur_expr, change_expr = size_m.group(1), cur_m.group(1), change_m.group(1)
    # 从 current-change 表达式取刷新的函数调用：形如 (p) => { q.pageNum = p; load() }
    calls = re.findall(r';?\s*([A-Za-z_$][\w$]*)\s*\(\s*\)\s*\}?\s*$', change_expr)
    loader = calls[-1] if calls else None
    if not loader:
        # 形如 (p) => { pageNum = p; reload() }
        calls = re.findall(r';\s*([A-Za-z_$][\w$]*)\s*\(', change_expr)
        loader = calls[-1] if calls else None
    if not loader:
        skipped.append((fn, 'no loader'))
        continue
    new_tag = tag
    # layout 增加 sizes
    lm = re.search(r'layout="([^"]*)"', new_tag)
    if lm:
        layout = lm.group(1)
        if 'sizes' not in layout:
            parts = [x.strip() for x in layout.split(',')]
            if 'total' in parts:
                parts.insert(parts.index('total') + 1, 'sizes')
            else:
                parts.insert(0, 'sizes')
            new_tag = new_tag.replace(lm.group(0), 'layout="%s"' % ', '.join(parts))
    # 插入 page-sizes 与 size-change（放在 total 之后或标签末尾）
    insert = ' :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { %s = s; %s = 1; %s() }"' % (
        size_expr, cur_expr, loader)
    if new_tag.rstrip().endswith('/>'):
        new_tag = new_tag.rstrip()[:-2] + insert + ' />'
    else:
        new_tag = new_tag[:-1] + insert + '>'
    s = s.replace(tag, new_tag, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    changed.append((fn, size_expr, cur_expr, loader))

print('已补充 %d 个页面' % len(changed))
for c in changed:
    print('  ', c)
print('跳过 %d 个' % len(skipped))
for c in skipped:
    print('  ', c)
