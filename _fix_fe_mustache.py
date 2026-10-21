# -*- coding: utf-8 -*-
"""修正生成页面里被原样输出的 mustache 转义标记"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend\src\views'
FILES = ['Persons', 'Spaces', 'Terminations', 'Appeals', 'Credits', 'Exchanges',
         'Complaints', 'Visits', 'ShortRent', 'HouseCalendar', 'GovReport', 'OpenApps']

BAD1 = "{{ '{{' }} JSON.stringify(row, null, 2) {{ '}}' }}"
GOOD1 = '{{ JSON.stringify(row, null, 2) }}'
BAD2 = "{{ '{{' }} JSON.stringify(detail, null, 2) {{ '}}' }}"
GOOD2 = '{{ JSON.stringify(detail, null, 2) }}'

n = 0
for f in FILES:
    p = os.path.join(BASE, f + '.vue')
    s = io.open(p, encoding='utf-8').read()
    before = s
    s = s.replace(BAD1, GOOD1).replace(BAD2, GOOD2)
    if s != before:
        io.open(p, 'w', encoding='utf-8').write(s)
        n += 1
print('修正 %d 个文件' % n)
