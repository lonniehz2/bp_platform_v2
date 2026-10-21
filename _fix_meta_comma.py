# -*- coding: utf-8 -*-
"""修正空 meta 插入产生的 `{, group: ...}` 语法错误"""
import io
import re

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

before = s.count('{,')
s = s.replace('meta: {,', 'meta: {')
s = re.sub(r'\{\s*,\s*group:', '{ group:', s)
after = s.count('{,')

io.open(R, 'w', encoding='utf-8').write(s)
print('修正 %d 处空 meta 逗号（残留 %d）' % (before - after, after))

# 打印所有 meta 行以便核对
print('\n修正后 meta 行：')
for m in re.finditer(r"path:\s*'([^']+)'[\s\S]{0,200}?meta:\s*\{([^}]*)\}", s):
    path, meta = m.group(1), m.group(2)
    if 'group' in meta:
        g = re.search(r"group:\s*'([^']+)'", meta)
        t = re.search(r"title:\s*'([^']+)'", meta)
        print('  %-18s %-12s %s' % (path, g.group(1) if g else '-',
                                    t.group(1) if t else ''))
