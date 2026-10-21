# -*- coding: utf-8 -*-
"""扫描：下拉框/单选项把枚举值直接当 label 显示"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

# 1) :label="x" 且 :value="x"（同一个变量 → 说明 label 就是编码）
same_var = []
# 2) :label="s" / :label="o" 这类可疑单字母变量
suspect = []

for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    page = f[:-4]
    for m in re.finditer(r'<el-option[^>]*:label="([^"]+)"[^>]*:value="([^"]+)"', s):
        lab, val = m.group(1).strip(), m.group(2).strip()
        if lab == val:
            same_var.append((page, lab))
    for m in re.finditer(r'<el-option[^>]*:label="([^"]+)"', s):
        lab = m.group(1).strip()
        if re.fullmatch(r'[a-z]', lab) or re.fullmatch(r'item|opt|row', lab):
            suspect.append((page, lab))

# 3) 脚本里以纯枚举字符串数组作选项的
strarrays = []
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    for m in re.finditer(r"const (\w+)\s*=\s*\[([^\]]*'[A-Z][A-Z_0-9]*'[^\]]*)\]", s):
        strarrays.append((f[:-4], m.group(1), m.group(2)[:80].replace('\n', ' ')))

print('=' * 70)
print(' ① :label 与 :value 绑定同一变量（label 显示编码）：%d 处' % len(same_var))
print('=' * 70)
by = {}
for p, v in same_var:
    by.setdefault(p, []).append(v)
for p in sorted(by):
    print('  %-16s %s' % (p, ', '.join(sorted(set(by[p])))))

print('\n' + '=' * 70)
print(' ② 单字母/泛用变量作 label（需人工确认）：%d 处' % len(suspect))
print('=' * 70)
by2 = {}
for p, v in suspect:
    by2.setdefault(p, []).append(v)
for p in sorted(by2):
    print('  %-16s %s' % (p, ', '.join(sorted(set(by2[p])))))

print('\n' + '=' * 70)
print(' ③ 纯枚举字符串数组（下拉数据源）：%d 处' % len(strarrays))
print('=' * 70)
for p, name, txt in strarrays:
    print('  %-16s %-22s [%s]' % (p, name, txt[:70]))
