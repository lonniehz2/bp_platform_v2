# -*- coding: utf-8 -*-
"""扫描：el-dialog / el-drawer 是否被误放进表格列插槽。

症状：弹窗写进 <el-table-column> 的 #default 插槽里 → 每行渲染一个弹窗，
遮罩层叠加，页面整体变黑且点击无响应。

规则：弹窗开始标签出现在 <el-table 之后、</el-table> 之前即判定为嵌套。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = os.path.join(HERE, '..', 'frontend', 'src', 'views')

DIALOG = re.compile(r'<el-(dialog|drawer)\b')

bad = []
for fn in sorted(os.listdir(VIEWS)):
    if not fn.endswith('.vue'):
        continue
    p = os.path.join(VIEWS, fn)
    src = io.open(p, encoding='utf-8', errors='replace').read()
    if '<el-table' not in src:
        continue
    for tbl in re.finditer(r'<el-table\b', src):
        end = src.find('</el-table>', tbl.start())
        if end < 0:
            continue
        for d in DIALOG.finditer(src, tbl.start(), end):
            line = src[:d.start()].count('\n') + 1
            bad.append('%s:%d  弹窗嵌套在表格列内' % (fn, line))

print('=' * 62)
print('弹窗嵌套扫描：检查 %d 个页面' % len([f for f in os.listdir(VIEWS)
                                          if f.endswith('.vue')]))
if not bad:
    print('  ✔ 未发现弹窗嵌套在表格列内')
    print('=' * 62)
    sys.exit(0)
print('  发现 %d 处：' % len(bad))
for b in bad:
    print('    ✗ ' + b)
print('=' * 62)
sys.exit(1)
