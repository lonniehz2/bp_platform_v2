# -*- coding: utf-8 -*-
"""注册 16 个新页面路由与菜单"""
import io
import os

P = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(P, encoding='utf-8').read()

if '/persons' in s:
    print('已注册，跳过')
    raise SystemExit

NEW = [
    ('persons', 'Persons', '人员档案', 'UserFilled'),
    ('spaces', 'Spaces', '空间层级', 'Grid'),
    ('terminations', 'Terminations', '退租管理', 'CircleClose'),
    ('appeals', 'Appeals', '申诉管理', 'ChatLineSquare'),
    ('credits', 'Credits', '信用惩戒', 'WarningFilled'),
    ('exchanges', 'Exchanges', '换房管理', 'Switch'),
    ('complaints', 'Complaints', '投诉管理', 'BellFilled'),
    ('visits', 'Visits', '来访登记', 'Postcard'),
    ('short-rent', 'ShortRent', '短租订单', 'Calendar'),
    ('house-calendar', 'HouseCalendar', '日房态', 'Date'),
    ('gov', 'GovReport', '监管报送', 'Promotion'),
    ('open', 'OpenApps', '开放平台', 'Connection'),
    ('rbac', 'Rbac', '用户与权限', 'Lock'),
    ('sys', 'SysAdmin', '系统支撑', 'Setting'),
]

items = []
for path, comp, title, icon in NEW:
    items.append('''  {
    path: '/%s',
    name: '%s',
    component: () => import('@/views/%s.vue'),
    meta: { title: '%s', icon: '%s' }
  }''' % (path, path.replace('-', ''), comp, title, icon))

anchor = '''  {
    path: '/grants',
    name: 'grants',
    component: () => import('@/views/Grants.vue'),
    meta: { title: '授权与对账', icon: 'Link' }
  }
]'''
assert anchor in s, '锚点缺失'
s = s.replace(anchor,
              '''  {
    path: '/grants',
    name: 'grants',
    component: () => import('@/views/Grants.vue'),
    meta: { title: '授权与对账', icon: 'Link' }
  },
''' + ',\n'.join(items) + '\n]', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('已注册 %d 个路由，文件行数 %d' % (len(NEW), len(s.split('\n'))))
