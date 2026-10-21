# -*- coding: utf-8 -*-
"""验证字段字典接口 + 全量检查详情字段是否都有中文名"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}


r = get('/api/v1/sys/field-labels')
labels = r.get('data') or {}
print('■ 字段字典接口：%s，共 %d 个字段' % (r.get('code'), len(labels)))

print('\n你提到的字段：')
for k in ('standardId', 'payMode', 'subsidyMode', 'subsidyPeriod', 'subsidyAmount',
          'recordStatus', 'recordNo', 'personId', 'orgId', 'contractId'):
    print('   %-16s → %s' % (k, labels.get(k, '（缺）')))

# 全量：抓多个列表接口，检查每个字段是否都有中文名
ENDPOINTS = [
    '/api/v1/fin/subsidies/records', '/api/v1/applications', '/api/v1/contracts',
    '/api/v1/fin/bills', '/api/v1/fin/deposits', '/api/v1/fin/refunds',
    '/api/v1/fin/cash-flows', '/api/v1/fin/fee-items', '/api/v1/workorders',
    '/api/v1/alerts', '/api/v1/appeals', '/api/v1/credits', '/api/v1/exchanges',
    '/api/v1/complaints', '/api/v1/visits', '/api/v1/short-rent-orders',
    '/api/v1/keyring', '/api/v1/terminations', '/api/v1/annual-reviews',
    '/api/v1/publicities', '/api/v1/allocation/allocations',
    '/api/v1/allocation/waiting', '/api/v1/house-calendar', '/api/v1/persons',
    '/api/v1/houses', '/api/v1/orgs', '/api/v1/devices', '/api/v1/gov/reports',
]
SKIP = {'id', 'tenantId'}

missing = {}
for path in ENDPOINTS:
    sep = '&' if '?' in path else '?'
    resp = get('%s%spageNum=1&pageSize=2' % (path, sep))
    data = resp.get('data')
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    if not rows:
        continue
    for k in rows[0]:
        if k.endswith('Label') or k.endswith('Name') or k in SKIP:
            continue
        if k not in labels:
            missing.setdefault(k, set()).add(path.split('/')[-1])

print('\n■ 字典未覆盖的字段：%d 个' % len(missing))
for k in sorted(missing):
    print('   %-24s %s' % (k, ', '.join(sorted(missing[k]))[:60]))
