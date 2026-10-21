# -*- coding: utf-8 -*-
"""造财务对账 + 最终统计"""
import json
import urllib.error
import urllib.request
from datetime import date

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('■ 财务对账')
for typ in ('DAILY', 'CHANNEL', 'BILL'):
    st, r = call('POST', '/api/v1/fin/reconciles', {
        'orgId': ORG, 'reconcileDate': '2026-11-01', 'reconcileType': typ,
        'channel': 'BANK', 'remark': '自动测试'})
    print('  %-8s %s %s %s' % (typ, st, r.get('code'), str(r.get('message'))[:56]))
    if r.get('code') == 'BP00000':
        break

print('\n■ 最终数据统计')
TARGETS = [
    ('合同变更', '/contract-changes'), ('财务对账', '/fin/reconciles'),
    ('规则集', '/rules/rulesets'), ('消息待办', '/messages/todos'),
    ('对账差异', '/grant-reconcile/diffs'), ('开放应用', '/open/apps'),
    ('监管报送', '/gov/reports'), ('政务适配器', '/gov/adapters'),
    ('短租订单', '/short-rent-orders'), ('通行授权', '/grants'),
    ('退租', '/terminations'), ('申诉', '/appeals'), ('信用', '/credits'),
    ('换房', '/exchanges'), ('投诉', '/complaints'), ('工单', '/workorders'),
    ('钥匙包', '/keyring'), ('告警', '/alerts'),
]
filled = 0
for name, path in TARGETS:
    sep = '?' if '?' not in path else '&'
    st, r = call('GET', '/api/v1%s%spageNum=1&pageSize=5' % (path, sep))
    d = r.get('data')
    if isinstance(d, dict):
        t = d.get('total')
        n = int(t) if t not in (None, '') else len(d.get('rows') or [])
    elif isinstance(d, list):
        n = len(d)
    else:
        n = 0
    filled += 1 if n else 0
    print('  %-8s %-4s %s' % (name, n, r.get('code')))
print('\n有数据 %d / %d' % (filled, len(TARGETS)))
