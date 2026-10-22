# -*- coding: utf-8 -*-
"""把三页操作列宽度从 490 收到 424（6 个中文按钮的实际需要）。"""
import io
import os
import re

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')
for fn in ['Terminations.vue', 'Alerts.vue', 'Exchanges.vue']:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    new = re.sub(r'(label="操作"[^>]*?)width="490"', r'\1width="424"', s, count=1)
    if new != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(new)
        print(fn, '→ 424')
    else:
        print(fn, '未匹配 490')
