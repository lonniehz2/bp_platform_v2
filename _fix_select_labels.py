# -*- coding: utf-8 -*-
"""修复：状态筛选下拉的 label 由编码改为中文"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

# 需要补充的枚举（下拉里出现、字典里可能没有的）
EXTRA = {
    'ASSIGNED': '已派单',
    'FINISHED': '已完成',
    'MAINTENANCE': '维护中',
    'CHANGING': '变更中',
    'SUPPLEMENT': '待补正',
    'DRAFT_REVIEW': '待审核',
}

# 1) 补枚举字典
E = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'
es = io.open(E, encoding='utf-8').read()
added = []
for k, v in EXTRA.items():
    if re.search(r"^\s*'?%s'?\s*:" % k, es, re.M) is None:
        added.append((k, v))
if added:
    block = '\n  // ---------- 补充（筛选下拉用） ----------\n'
    for k, v in added:
        block += "  %s: '%s',\n" % (k, v)
    es = es.replace('  // ---------- 房源 / 空间 ----------',
                    block + '\n  // ---------- 房源 / 空间 ----------', 1)
    io.open(E, 'w', encoding='utf-8').write(es)
    print('  ✓ enums.js 补 %d 个枚举：%s'
          % (len(added), ', '.join(k for k, _ in added)))

# 2) 各页面：:label="s" → :label="enumLabel(null, s)"
TARGETS = ['Applications', 'Bills', 'Contracts', 'Houses', 'WorkOrders', 'SysAdmin']
fixed = 0
for name in TARGETS:
    p = os.path.join(V, name + '.vue')
    s = io.open(p, encoding='utf-8').read()
    orig = s

    # 只替换 el-option 里的 :label="单字母"
    def fix_label(m):
        return m.group(0).replace(m.group(1), 'enumLabel(null, %s)' % m.group(2))

    s = re.sub(r'(:label=")([a-z])(")', lambda m: ':label="enumLabel(null, %s)"' % m.group(2), s)

    if s != orig:
        if "from '@/constants/enums'" not in s:
            if '<script setup>' in s:
                i = s.find('<script setup>') + len('<script setup>')
                s = s[:i] + "\nimport { enumLabel } from '@/constants/enums'" + s[i:]
        io.open(p, 'w', encoding='utf-8').write(s)
        fixed += 1
        m = re.search(r'<el-option[^>]*:label="enumLabel\(null, \w\)"[^>]*>', s)
        print('  ✓ %-14s %s' % (name, m.group(0)[:96] if m else ''))

print('\n  共修复 %d 个页面' % fixed)
