# -*- coding: utf-8 -*-
"""用真实路径造数：合同变更/规则集/开放应用/政务适配器+报送/财务对账"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
CONTRACT = (D.get('contracts') or [{}])[0].get('id')


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

TRIES = [
    ('合同变更', '/api/v1/contracts/%s/changes' % CONTRACT,
     {'changeType': 'RENT', 'newMonthlyRent': 1200, 'reason': '年审调租',
      'effectiveDate': '2026-12-01'}),
    ('规则集', '/api/v1/rules/rulesets',
     {'code': 'RS001', 'name': '欠费阈值规则集', 'domain': 'FINANCE',
      'scenario': 'ARREAR', 'securityType': 'PUBLIC', 'ruleVersion': 'v1',
      'description': '自动测试规则集'}),
    ('开放应用', '/api/v1/open/apps',
     {'appName': '测试开放应用', 'appCode': 'APP_TEST_1', 'appType': 'PARTNER',
      'contactName': '张三', 'contactPhone': '13800138000',
      'callbackUrl': 'https://example.com/cb', 'remark': '自动测试'}),
    ('政务适配器', '/api/v1/gov/adapters',
     {'adapterCode': 'ADP001', 'adapterName': '市住建局适配器',
      'systemType': 'HOUSING', 'protocol': 'HTTP', 'endpoint': 'https://gov.example.com/api',
      'authType': 'TOKEN', 'tokenValue': 'tk_test', 'status': 'ENABLED'}),
    ('财务对账', '/api/v1/fin/reconciles',
     {'orgId': ORG, 'reconcileDate': '2026-11-01', 'reconcileType': 'DAILY',
      'channel': 'BANK', 'channelAmount': 5625.00, 'systemAmount': 5625.00,
      'remark': '自动测试对账'}),
]

print('=' * 74)
for label, path, body in TRIES:
    st, r = call('POST', path, body)
    print('■ %-8s %-40s → %s %s'
          % (label, path.replace('/api/v1', ''), r.get('code'),
             str(r.get('message'))[:56]))

print('\n■ 政务报送（需先有适配器）')
for typ in ('MONTHLY', 'ANNUAL', 'RENT'):
    st, r = call('POST', '/api/v1/gov/reports', {
        'targetSystem': 'HOUSING', 'reportType': typ,
        'reportPeriod': '2026-11', 'reportData': '{}', 'orgId': ORG})
    print('  %-8s %s %s %s' % (typ, st, r.get('code'), str(r.get('message'))[:58]))
    if r.get('code') == 'BP00000':
        break

print('\n■ 校验')
for name, path in (('合同变更', '/api/v1/contract-changes?pageNum=1&pageSize=5'),
                   ('规则集', '/api/v1/rules/rulesets'),
                   ('开放应用', '/api/v1/open/apps'),
                   ('政务适配器', '/api/v1/gov/adapters'),
                   ('监管报送', '/api/v1/gov/reports?pageNum=1&pageSize=5'),
                   ('财务对账', '/api/v1/fin/reconciles?pageNum=1&pageSize=5')):
    st, r = call('GET', path)
    d = r.get('data')
    if isinstance(d, dict):
        t = d.get('total')
        n = int(t) if t not in (None, '') else len(d.get('rows') or [])
    elif isinstance(d, list):
        n = len(d)
    else:
        n = 0
    print('  %-8s %s 条 %s' % (name, n, r.get('code')))
