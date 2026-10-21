# -*- coding: utf-8 -*-
"""把绑定 ID 字段的 v-model.number 改为 v-model

原因：19 位雪花 ID 超过 JS double 的安全整数范围（2^53-1），
v-model.number 会把 1000000000000012161 舍入成 1000000000000012200，
导致表单提交的 ID 与实际记录不符（合同挂到不存在的房源上）。

只处理「字段名以 Id 结尾」或 hid/pid 这类主键字段；金额、面积、
人口数等仍保留 .number。
"""
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')
ID_EXTRA = {'hid', 'pid'}
AMOUNT_OK = {'Amount', 'Months', 'Multiplier', 'Size', 'Area', 'Day', 'Income'}

pat = re.compile(r'v-model\.number="([^"]+)"')


def last_ident(expr):
    m = re.findall(r'[A-Za-z_$][\w$]*', expr)
    return m[-1] if m else ''


def is_id(expr):
    name = last_ident(expr)
    if name in ID_EXTRA:
        return True
    return name.endswith('Id')


changed = []
for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        if not fn.endswith('.vue'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding='utf-8') as f:
            src = f.read()
        hits = []

        def repl(m):
            expr = m.group(1)
            if is_id(expr):
                hits.append(expr)
                return 'v-model="%s"' % expr
            return m.group(0)

        out = pat.sub(repl, src)
        if out != src:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(out)
            changed.append((os.path.relpath(path, ROOT), hits))

if not changed:
    print('没有需要修改的文件')
else:
    total = 0
    for rel, hits in changed:
        print('%-34s %d 处：%s' % (rel, len(hits), ', '.join(sorted(set(hits)))))
        total += len(hits)
    print('\n共修改 %d 个文件、%d 处 ID 绑定' % (len(changed), total))
