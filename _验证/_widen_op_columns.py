# -*- coding: utf-8 -*-
"""退租 / 告警 / 换房：加宽操作列，保证所有按钮一行显示（不改下拉）。

宽度估算：每个文字按钮约 76px（含间距），外加左右内边距 36px，向上取整到 10。
只增不减：若现有宽度已足够则保持原值。
"""
import io
import os
import re

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')
TARGETS = ['Terminations.vue', 'Alerts.vue', 'Exchanges.vue']

for fn in TARGETS:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'(<el-table-column[^>]*label="操作"[^>]*>)', s)
    if not m:
        print(fn, '未找到操作列')
        continue
    head = m.group(1)
    # 取该列到下个 </el-table-column> 的片段，统计按钮数
    seg_end = s.find('</el-table-column>', m.end())
    seg = s[m.end():seg_end if seg_end > 0 else m.end() + 2000]
    btns = len(re.findall(r'<el-button[^>]*', seg))
    need = int(round((btns * 76 + 36) / 10.0)) * 10
    cur = re.search(r'width="(\d+)"', head)
    cur_w = int(cur.group(1)) if cur else 0
    target = max(cur_w, need)
    if cur:
        new_head = head.replace('width="%d"' % cur_w, 'width="%d"' % target, 1)
    else:
        new_head = head.replace('label="操作"', 'label="操作" width="%d"' % target, 1)
    s = s[:m.start()] + new_head + s[m.end():]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%-20s 按钮 %d 个，宽度 %d → %d' % (fn, btns, cur_w, target))
