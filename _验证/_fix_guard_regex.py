# -*- coding: utf-8 -*-
"""重写 GUARD 正则（避免转义问题）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_race_pattern.py')
lines = io.open(P, encoding='utf-8').read().split('\n')

# 找到 GUARD = re.compile( 起始行，替换到该语句结束（含 re.I) 的行）
start = next(i for i, l in enumerate(lines) if l.startswith('GUARD = re.compile('))
end = start
while 're.I)' not in lines[end]:
    end += 1

GUARD_LINES = [
    "GUARD = re.compile('synchronized|lockForUpdate|for update|UpdateWrapper|setSql|'",
    "                   'computeIfAbsent|INSERT IGNORE|on duplicate key|'",
    "                   'DuplicateKeyException', re.I)"
]

lines[start:end + 1] = GUARD_LINES
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
print('GUARD 已重写为 %d 行' % len(GUARD_LINES))
