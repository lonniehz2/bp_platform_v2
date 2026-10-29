# -*- coding: utf-8 -*-
"""把页面内写死的白底/深灰字替换为 CSS 变量，适配深色模式。"""
import io
import os
import re

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
SKIP = {'Login.vue', 'Screen.vue', 'H5Login.vue'}

REPL = [
    ('background: #fff;', 'background: var(--bp-card-bg, #fff);'),
    ('background: #ffffff;', 'background: var(--bp-card-bg, #fff);'),
    ('background: #fff !important;', 'background: var(--bp-card-bg, #fff) !important;'),
    ('border: 1px solid #f0f0f0', 'border: 1px solid var(--el-border-color-light)'),
    ('border-bottom: 1px solid #f0f0f0', 'border-bottom: 1px solid var(--el-border-color-light)'),
    ('color: #303133', 'color: var(--el-text-color-primary)'),
    ('color: #606266', 'color: var(--el-text-color-regular)'),
    ('color: #909399', 'color: var(--el-text-color-secondary)'),
    ('color: rgba(0, 0, 0, 0.85)', 'color: var(--el-text-color-primary)'),
    ('color: rgba(0, 0, 0, 0.65)', 'color: var(--el-text-color-regular)'),
    ('color: rgba(0, 0, 0, 0.45)', 'color: var(--el-text-color-secondary)'),
]

changed = []
for fn in sorted(os.listdir(V)):
    if not fn.endswith('.vue') or fn in SKIP:
        continue
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    orig = s
    for a, b in REPL:
        s = s.replace(a, b)
    if s != orig:
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        changed.append(fn)
print('changed', len(changed))
print(', '.join(changed))
