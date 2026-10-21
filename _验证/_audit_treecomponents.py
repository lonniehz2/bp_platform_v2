# -*- coding: utf-8 -*-
"""检查所有树形/级联组件使用点"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
PAT = ['el-tree', 'el-tree-select', 'el-cascader', 'children', 'tree']

hits = {}
for root, _, files in os.walk(FE):
    for f in sorted(files):
        if not f.endswith(('.vue', '.js')):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        found = [k for k in ('el-tree', 'el-tree-select', 'el-cascader') if k in s]
        if found:
            hits[os.path.relpath(p, FE)] = found

print('=== 树形/级联组件使用点 ===')
for k, v in hits.items():
    print('  %-28s %s' % (k, ', '.join(v)))

print('\n=== 调用 tree 类接口的模块 ===')
for root, _, files in os.walk(FE):
    for f in sorted(files):
        if not f.endswith('.js'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        for m in re.finditer(r"['\"`]([^'\"`]*tree[^'\"`]*)['\"`]", s, re.I):
            print('  %-22s %s' % (f, m.group(1)))
