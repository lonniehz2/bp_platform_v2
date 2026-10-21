# -*- coding: utf-8 -*-
"""补齐 8 个模块的 API 封装 + 路由注册"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) API 封装补全 ----------
p = os.path.join(FE, 'api', 'modules.js')
s = io.open(p, encoding='utf-8').read()

ADD = '''
/** 补贴 / 押金 / 公示 / 轮候 / 计费 / 催缴 / 流水 / 合同变更（补齐 console 已有模块） */
export const subsidyApi = {
  records: (params) => req.get('/fin/subsidies/records', { params }),
  calc: (data) => req.post('/fin/subsidies/calc', data),
  standards: (params) => req.get('/fin/subsidies/standards', { params }),
  batchGrant: (data) => req.post('/fin/subsidies/records/batch', data),
  confirm: (id) => req.post(`/fin/subsidies/records/${id}/confirm`)
}

export const contractChangeApi = {
  page: (params) => req.get('/contract-changes', { params }),
  get: (id) => req.get(`/contract-changes/${id}`),
  approve: (id, data) => req.post(`/contract-changes/${id}/approve`, data)
}
'''

if 'subsidyApi' not in s:
    s = s.rstrip() + '\n' + ADD
if 'arrears:' not in s:
    # financeApi 补 arrears / cashflow
    s = s.replace(
        "  feeItems: (params) => req.get('/fin/fee-items', { params })",
        "  feeItems: (params) => req.get('/fin/fee-items', { params }),\n"
        "  arrears: (params) => req.get('/fin/arrears', { params }),\n"
        "  cashflow: (params) => req.get('/fin/cashflow', { params }),\n"
        "  refunds: (params) => req.get('/fin/refunds', { params })")
io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ modules.js 已补 subsidyApi / contractChangeApi / arrears / cashflow / refunds')

# ---------- 2) 路由注册 ----------
R = os.path.join(FE, 'router', 'index.js')
r = io.open(R, encoding='utf-8').read()

NEW = [('subsidies', 'Subsidies', '补贴管理', 'Coin'),
       ('deposits', 'Deposits', '押金与退款', 'Wallet'),
       ('publicities', 'Publicities', '公示管理', 'Notification'),
       ('waitlist', 'Waitlist', '轮候管理', 'Sort'),
       ('fee-items', 'FeeItems', '计费项目', 'PriceTag'),
       ('arrears', 'Arrears', '催缴管理', 'Bell'),
       ('cashflow', 'Cashflow', '资金流水', 'TrendCharts'),
       ('contract-changes', 'ContractChanges', '合同变更', 'EditPen')]

if "'/subsidies'" not in r:
    items = []
    for path, comp, title, icon in NEW:
        items.append('''  {
    path: '/%s',
    name: '%s',
    component: () => import('@/views/%s.vue'),
    meta: { title: '%s', icon: '%s' }
  }''' % (path, path.replace('-', ''), comp, title, icon))

    anchor = '''  {
    path: '/sys',
    name: 'sys',
    component: () => import('@/views/SysAdmin.vue'),
    meta: { title: '系统支撑', icon: 'Setting' }
  }
]'''
    assert anchor in r, '路由锚点缺失'
    r = r.replace(anchor,
                  '''  {
    path: '/sys',
    name: 'sys',
    component: () => import('@/views/SysAdmin.vue'),
    meta: { title: '系统支撑', icon: 'Setting' }
  },
''' + ',\n'.join(items) + '\n]', 1)
    io.open(R, 'w', encoding='utf-8').write(r)
    print('  ✓ 已注册 %d 个路由' % len(NEW))
else:
    print('  - 路由已存在')
