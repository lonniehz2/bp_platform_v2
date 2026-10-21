# -*- coding: utf-8 -*-
"""解析 console.html：抽取每个页签调用的真实接口，作为 SPA 补齐的精确规格"""
import io
import re
from collections import OrderedDict

P = r'D:\Work\业务平台开发\backend\src\main\resources\static\console.html'
s = io.open(P, encoding='utf-8').read()
print('console.html 大小 %.1f KB, %d 行' % (len(s) / 1024, s.count('\n')))

# ---- 1) 页签识别：尝试多种结构 ----
cands = [
    ('data-tab', re.findall(r'data-tab="([^"]+)"', s)),
    ('id=tab-', re.findall(r'id="tab-([a-zA-Z0-9_\-]+)"', s)),
    ('id=page-', re.findall(r'id="page-([a-zA-Z0-9_\-]+)"', s)),
    ('showTab(', re.findall(r"showTab\('([^']+)'\)", s)),
    ('nav item', re.findall(r'class="nav-item[^"]*"[^>]*>([^<]{1,20})<', s)),
]
for name, found in cands:
    uniq = list(OrderedDict.fromkeys(found))
    print('  %-10s 命中 %3d 个  例：%s' % (name, len(uniq), uniq[:8]))

# ---- 2) 接口调用 ----
calls = re.findall(r"bpFetch\(\s*[`'\"]([^`'\"]+)[`'\"]", s)
print('\nbpFetch 调用 %d 处' % len(calls))
paths = list(OrderedDict.fromkeys(c.split('?')[0] for c in calls))
print('去重接口 %d 个：' % len(paths))
for p in sorted(paths)[:40]:
    print('   ' + p)

# ---- 3) 按 section 归组（找 <section 或 <div id="xxx-panel"）----
print('\n=== 页面分块标签（h2/h3 文本，作为模块名）===')
heads = re.findall(r'<h[23][^>]*>([^<]{2,40})</h[23]>', s)
for h in list(OrderedDict.fromkeys(heads))[:30]:
    print('   ' + h.strip())
