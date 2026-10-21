# -*- coding: utf-8 -*-
"""处理剩余 JSON.stringify 变体"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    if 'JSON.stringify' not in s:
        continue

    # 找出所有出现位置，逐个替换成 DetailView（变量名不同）
    def repl(m):
        var = m.group(1)
        return '<DetailView :row="%s || {}" />' % var

    s2 = re.sub(
        r'<pre class="raw">\s*\{\{\s*JSON\.stringify\(\s*(\w+)[^}]*\)\s*\}\}\s*</pre>',
        repl, s)

    # 兜底：任何残留的 JSON.stringify 包在 <pre> 里
    s2 = re.sub(
        r'<pre[^>]*>\s*\{\{\s*JSON\.stringify\([^}]*\)\s*\}\}\s*</pre>',
        lambda m: '<DetailView :row="detail || current || row || {}" />', s2)

    if s2 != s:
        if "from '@/components/DetailView.vue'" not in s2:
            i = s2.find('<script setup>')
            if i != -1:
                i += len('<script setup>')
                s2 = s2[:i] + "\nimport DetailView from '@/components/DetailView.vue'" + s2[i:]
        io.open(p, 'w', encoding='utf-8').write(s2)
        print('  ✓ %-16s 残留 %d → %d'
              % (f[:-4], s.count('JSON.stringify'), s2.count('JSON.stringify')))

print('\n最终检查：')
left = []
for f in os.listdir(V):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    if 'JSON.stringify' in s:
        left.append(f[:-4])
print('  仍含 JSON.stringify：%s' % (left or '无'))
