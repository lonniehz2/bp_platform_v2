# -*- coding: utf-8 -*-
"""前端消费后端补全字段：*IdName / *StatusLabel 等"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

# 列 prop="xxxId" → 优先显示 xxxIdName
ID_COLS = 0
files = 0
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    orig = s

    def repl(m):
        global ID_COLS
        indent, prop, attrs = m.group(1), m.group(2), m.group(3)
        # 跳过已有 template 的
        ID_COLS += 1
        return (f'{indent}<el-table-column{attrs}>\n'
                f'{indent}  <template #default="{{ row }}">'
                f'{{{{ row.{prop}Name || row.{prop} }}}}</template>\n'
                f'{indent}</el-table-column>')

    s = re.sub(r'( *)<el-table-column((?:[^>]*?)prop="(\w+Id)"(?:[^">]*"[^"]*")*) */>',
               lambda m: (m.group(1) + '<el-table-column' + m.group(2) + '>\n'
                          + m.group(1) + '  <template #default="{ row }">{{ row.'
                          + m.group(3) + 'Name || row.' + m.group(3) + ' }}</template>\n'
                          + m.group(1) + '</el-table-column>'),
               s)
    if s != orig:
        io.open(p, 'w', encoding='utf-8').write(s)
        files += 1

print('  ✓ ID 列改为优先显示名称：%d 个页面' % files)

# 枚举列：改为优先后端 label
ENUM_COLS = 0
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    orig = s
    s = re.sub(r"\{\{ enumLabel\('(\w+)', row\.\1\) \}\}",
               lambda m: '{{ row.%sLabel || enumLabel(\'%s\', row.%s) }}'
               % (m.group(1), m.group(1), m.group(1)), s)
    if s != orig:
        io.open(p, 'w', encoding='utf-8').write(s)
        ENUM_COLS += len(re.findall(r'row\.\w+Label \|\|', s))
print('  ✓ 枚举列优先使用后端 label')

total = 0
for f in os.listdir(V):
    if f.endswith('.vue'):
        s = io.open(os.path.join(V, f), encoding='utf-8').read()
        total += len(re.findall(r'row\.\w+Name \|\|', s))
print('  ✓ 名称回退已写入 %d 处' % total)
