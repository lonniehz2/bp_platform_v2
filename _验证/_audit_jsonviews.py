# -*- coding: utf-8 -*-
"""统计所有「原始 JSON」详情展示点"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

hits = []
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    spots = []
    if 'JSON.stringify(row' in s:
        spots.append('展开行')
    if 'JSON.stringify(detail' in s:
        spots.append('详情抽屉')
    if 'JSON.stringify(current' in s:
        spots.append('选中详情')
    if spots:
        hits.append((f[:-4], spots))

print('共 %d 个页面展示原始 JSON：' % len(hits))
for p, sp in hits:
    print('  %-18s %s' % (p, ', '.join(sp)))

total = sum(1 for f in os.listdir(V) if f.endswith('.vue')
            and 'JSON.stringify' in io.open(os.path.join(V, f), encoding='utf-8').read())
print('\n涉及文件：%d 个' % total)

# 收集所有 prop="x" label="Y" 映射，作为字段中文字典
FIELD = {}
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    for m in re.finditer(r'prop="(\w+)"\s+label="([^"]+)"', s):
        FIELD.setdefault(m.group(1), m.group(2))
print('\n可从模板提取的字段中文名：%d 个' % len(FIELD))
for k, v in list(FIELD.items())[:20]:
    print('   %-22s %s' % (k, v))
