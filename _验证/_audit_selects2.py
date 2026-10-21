# -*- coding: utf-8 -*-
"""深度检查：所有 el-select 的选项来源是否可能显示英文"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

print('=' * 72)
print(' 全部 el-option 的 label 绑定方式')
print('=' * 72)

buckets = {'已中文化': [], '显式中文': [], '可疑': []}
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    page = f[:-4]
    for m in re.finditer(r'<el-option([^>]*)>?', s):
        attrs = m.group(1)
        lm = re.search(r':?label="([^"]+)"', attrs)
        if not lm:
            continue
        lab = lm.group(1).strip()
        if 'enumLabel' in lab or 'dictTypeLabel' in lab:
            buckets['已中文化'].append((page, lab))
        elif re.search(r'[\u4e00-\u9fa5]', lab):
            buckets['显式中文'].append((page, lab))
        elif lab in ('o.label', 'opt.label', 'item.label', 's.label'):
            buckets['显式中文'].append((page, lab))
        else:
            buckets['可疑'].append((page, lab))

for k, v in buckets.items():
    print('\n【%s】%d 处' % (k, len(v)))
    by = {}
    for p, l in v:
        by.setdefault(p, set()).add(l)
    for p in sorted(by):
        print('   %-16s %s' % (p, ', '.join(sorted(by[p]))[:90]))

# 2) 检查硬编码英文 label
print('\n' + '=' * 72)
print(' 硬编码英文 label 的 el-option')
print('=' * 72)
n = 0
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    for m in re.finditer(r'<el-option\s+label="([A-Za-z][^"]*)"', s):
        n += 1
        print('   %-16s label="%s"' % (f[:-4], m.group(1)))
if not n:
    print('   无')
