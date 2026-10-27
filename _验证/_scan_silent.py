# -*- coding: utf-8 -*-
"""扫描写操作缺少 catch 的页面（静默失败风险）。"""
import io
import os
import re

VIEWS = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                     'frontend', 'src', 'views')

pat = re.compile(r'await (?:req|\w+Api)\.(?:post|put|delete)\(')
for f in sorted(os.listdir(VIEWS)):
    if not f.endswith('.vue'):
        continue
    lines = io.open(os.path.join(VIEWS, f), encoding='utf-8', errors='replace').read().split('\n')
    for i, l in enumerate(lines):
        if pat.search(l):
            window = '\n'.join(lines[max(0, i - 12):i + 12])
            if 'catch' not in window:
                print('%s:%d  %s' % (f, i + 1, l.strip()[:90]))
