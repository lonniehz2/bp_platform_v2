# -*- coding: utf-8 -*-
"""菜单组内按业务流程排序"""
import io
import re

L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
s = io.open(L, encoding='utf-8').read()

RANK = '''/**
 * 组内顺序：按业务流程，而不是路由定义顺序。
 * 例如「资格准入」应先是人员建档，再是申请、轮候、公示、年审。
 */
const MENU_RANK = {
  '/dashboard': 1, '/reports': 2,

  '/persons': 10, '/applications': 11, '/waitlist': 12,
  '/publicities': 13, '/annual-reviews': 14,

  '/allocations': 20, '/contracts': 21, '/contract-changes': 22,
  '/exchanges': 23,

  '/fee-items': 30, '/bills': 31, '/deposits': 32, '/arrears': 33,
  '/subsidies': 34, '/cashflow': 35,

  '/terminations': 40, '/credits': 41, '/appeals': 42,

  '/houses': 50, '/spaces': 51, '/house-calendar': 52, '/short-rent': 53,
  '/devices': 54, '/access': 55, '/keyring': 56, '/grants': 57,

  '/workorders': 60, '/alerts': 61, '/complaints': 62, '/visits': 63,
  '/messages': 64,

  '/orgs': 70, '/rbac': 71, '/sys': 72, '/ops-center': 73,
  '/open': 74, '/gov': 75
}

'''

if 'MENU_RANK' not in s:
    s = s.replace('const GROUP_ORDER = [', RANK + 'const GROUP_ORDER = [', 1)

    # 分组计算里加入排序
    s = s.replace('''    const items = menus.value.filter((m) => (m.meta?.group || '其他') === name)
    if (items.length) out.push({ name, icon: GROUP_ICON[name] || 'Menu', items })''',
                  '''    const items = menus.value
      .filter((m) => (m.meta?.group || '其他') === name)
      .sort((a, b) => (MENU_RANK[a.path] || 999) - (MENU_RANK[b.path] || 999))
    if (items.length) out.push({ name, icon: GROUP_ICON[name] || 'Menu', items })''', 1)

    io.open(L, 'w', encoding='utf-8').write(s)
    print('  ✓ Layout：加入组内业务排序（MENU_RANK）')
else:
    print('  - 已存在排序逻辑')

# 校验关键代码
out = io.open(L, encoding='utf-8').read()
for kw in ('MENU_RANK', 'MENU_RANK[a.path]', 'GROUP_ORDER'):
    print('   %-18s %s' % (kw, '✓' if kw in out else '✗'))
