# -*- coding: utf-8 -*-
"""把 21 个页面的原始 JSON 详情替换为 DetailView 组件"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

files = [f for f in sorted(os.listdir(V)) if f.endswith('.vue')]
patched = []
for f in files:
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    if 'JSON.stringify' not in s:
        continue
    orig = s

    # 1) 展开行：<pre class="raw">{{ JSON.stringify(row, null, 2) }}</pre>
    s = re.sub(
        r'<pre class="raw">\{\{\s*JSON\.stringify\(\s*row\s*,\s*null\s*,\s*2\s*\)\s*\}\}</pre>',
        '<DetailView :row="row" />', s)
    # 2) 详情抽屉 / 选中详情
    s = re.sub(
        r'<pre class="raw">\{\{\s*JSON\.stringify\(\s*(detail|current)\s*,\s*null\s*,\s*2\s*\)\s*\}\}</pre>',
        r'<DetailView :row="\1 || {}" />', s)
    # 3) 带其他格式的变体（可能有换行/缩进）
    s = re.sub(
        r'<pre class="raw">\s*\{\{\s*JSON\.stringify\(\s*(\w+)\s*,\s*null\s*,\s*2\s*\)\s*\}\}\s*</pre>',
        r'<DetailView :row="\1 || {}" />', s)

    if s == orig:
        continue

    # 4) 注入 import
    if 'DetailView' in s and "from '@/components/DetailView.vue'" not in s:
        i = s.find('<script setup>')
        if i != -1:
            i += len('<script setup>')
            s = s[:i] + "\nimport DetailView from '@/components/DetailView.vue'" + s[i:]

    io.open(p, 'w', encoding='utf-8').write(s)
    patched.append((f[:-4], s.count('<DetailView')))

print('已替换 %d 个页面：' % len(patched))
for name, n in patched:
    print('  %-18s %d 处' % (name, n))

# 检查残留
left = []
for f in os.listdir(V):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    if 'JSON.stringify' in s:
        left.append((f[:-4], s.count('JSON.stringify')))
print('\n仍有 JSON.stringify 的页面：%s' % (left or '无'))
