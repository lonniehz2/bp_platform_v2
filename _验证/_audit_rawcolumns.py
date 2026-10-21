# -*- coding: utf-8 -*-
"""全量扫描：页面中显示原始枚举/ID 的列"""
import io
import os
import re
from collections import defaultdict

V = r'D:\Work\业务平台开发\frontend\src\views'

ENUM_SUFFIX = (r'(?:Status|Type|Stage|Mode|Level|Channel|Result|Source|Way|'
               r'Category|Kind)')
ID_SUFFIX = r'(?:Id)'

enum_hits = defaultdict(list)
id_hits = defaultdict(list)

for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    page = f[:-4]

    # 1) 直接以 prop="xxxStatus" 显示枚举
    for m in re.finditer(r'prop="(\w*%s)"\s+label="([^"]+)"' % ENUM_SUFFIX, s):
        enum_hits[page].append((m.group(1), m.group(2)))

    # 2) 直接以 prop="xxxId" 显示 ID（应为名称）
    for m in re.finditer(r'prop="(\w*%s)"\s+label="([^"]+)"' % ID_SUFFIX, s):
        id_hits[page].append((m.group(1), m.group(2)))

    # 3) {{ row.xxxStatus }} 形式
    for m in re.finditer(r'\{\{\s*row\.(\w*%s)\s*\}\}' % ENUM_SUFFIX, s):
        enum_hits[page].append((m.group(1), '模板插值'))

print('=' * 72)
print(' ① 直接显示枚举原始值的列：%d 个页面，%d 处'
      % (len([k for k in enum_hits if enum_hits[k]]),
         sum(len(v) for v in enum_hits.values())))
print('=' * 72)
for page in sorted(enum_hits):
    print('\n■ %s' % page)
    for field, label in enum_hits[page]:
        print('    %-26s → %s' % (field, label))

print('\n' + '=' * 72)
print(' ② 直接显示 ID 而非名称的列：%d 个页面，%d 处'
      % (len([k for k in id_hits if id_hits[k]]),
         sum(len(v) for v in id_hits.values())))
print('=' * 72)
for page in sorted(id_hits):
    print('\n■ %s' % page)
    for field, label in id_hits[page]:
        print('    %-26s → %s' % (field, label))
