# -*- coding: utf-8 -*-
"""用 RENT_ADJUST 补合同变更 + 最终全量核对"""
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

print('■ 合同变更（RENEW|RENT_ADJUST|PERIOD|LESSEE|OTHER）')
for typ in ('RENT_ADJUST', 'PERIOD', 'LESSEE', 'OTHER'):
    st, r = call('POST', '/api/v1/contracts/%s/changes' % CONTRACT, {
        'changeType': typ,
        'newMonthlyRent': 1250 if typ == 'RENT_ADJUST' else None,
        'reason': '自动测试变更',
        'effectiveDate': '2026-12-01'})
    print('  %-11s %s %s %s' % (typ, st, r.get('code'), str(r.get('message'))[:56]))
    if r.get('code') == 'BP00000':
        break

# ---------------- 最终全量核对 ----------------
ORGID = ORG
PAGES = [
    ('运营驾驶舱', '/api/v1/rpt/screens/OVERVIEW/data'),
    ('组织机构', '/api/v1/orgs?pageNum=1&pageSize=5'),
    ('空间树', '/api/v1/spaces/tree?orgId=%s' % ORGID),
    ('房源', '/api/v1/houses?pageNum=1&pageSize=5'),
    ('人员', '/api/v1/persons?pageNum=1&pageSize=5'),
    ('保障档案', '/api/v1/guarantee-profiles?pageNum=1&pageSize=5'),
    ('实名认证', '/api/v1/verify-records?pageNum=1&pageSize=5'),
    ('申请', '/api/v1/applications?pageNum=1&pageSize=5'),
    ('公示', '/api/v1/publicities?pageNum=1&pageSize=5'),
    ('轮候', '/api/v1/allocation/waiting?pageNum=1&pageSize=5'),
    ('批次', '/api/v1/allocation/batches?pageNum=1&pageSize=5'),
    ('配租单', '/api/v1/allocation/allocations?pageNum=1&pageSize=5'),
    ('合同', '/api/v1/contracts?pageNum=1&pageSize=5'),
    ('合同变更', '/api/v1/contract-changes?pageNum=1&pageSize=5'),
    ('年审', '/api/v1/annual-reviews?pageNum=1&pageSize=5'),
    ('退租', '/api/v1/terminations?pageNum=1&pageSize=5'),
    ('账单', '/api/v1/fin/bills?pageNum=1&pageSize=5'),
    ('收款', '/api/v1/fin/payments?pageNum=1&pageSize=5'),
    ('押金', '/api/v1/fin/deposits?pageNum=1&pageSize=5'),
    ('退款', '/api/v1/fin/refunds?pageNum=1&pageSize=5'),
    ('补贴', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=5'),
    ('计费项目', '/api/v1/fin/fee-items?pageNum=1&pageSize=5'),
    ('催缴', '/api/v1/fin/dunnings?pageNum=1&pageSize=5'),
    ('资金流水', '/api/v1/fin/cash-flows?pageNum=1&pageSize=5'),
    ('财务对账', '/api/v1/fin/reconciles?pageNum=1&pageSize=5'),
    ('工单', '/api/v1/workorders?pageNum=1&pageSize=5'),
    ('告警', '/api/v1/alerts?pageNum=1&pageSize=5'),
    ('规则集', '/api/v1/rules/rulesets'),
    ('设备', '/api/v1/devices?pageNum=1&pageSize=5'),
    ('通行记录', '/api/v1/access-records?pageNum=1&pageSize=5'),
    ('报表', '/api/v1/rpt/reports'),
    ('大屏', '/api/v1/rpt/screens'),
    ('钥匙包', '/api/v1/keyring?pageNum=1&pageSize=5'),
    ('通行授权', '/api/v1/grants?pageNum=1&pageSize=5'),
    ('用户权限', '/api/v1/rbac/users?pageNum=1&pageSize=5'),
    ('审计日志', '/api/v1/sys/audit-logs?pageNum=1&pageSize=5'),
    ('字典', '/api/v1/sys/dicts/HOUSE_TYPE'),
    ('开放应用', '/api/v1/open/apps'),
    ('开放接口', '/api/v1/open/apis'),
    ('监管报送', '/api/v1/gov/reports?pageNum=1&pageSize=5'),
    ('政务适配器', '/api/v1/gov/adapters'),
    ('短租订单', '/api/v1/short-rent-orders?pageNum=1&pageSize=5'),
    ('申诉', '/api/v1/appeals?pageNum=1&pageSize=5'),
    ('信用', '/api/v1/credits?pageNum=1&pageSize=5'),
    ('换房', '/api/v1/exchanges?pageNum=1&pageSize=5'),
    ('投诉', '/api/v1/complaints?pageNum=1&pageSize=5'),
]

print('\n' + '=' * 70)
print(' 最终全量核对')
print('=' * 70)
okc, empty, fail = 0, [], []
for name, path in PAGES:
    st, r = call('GET', path)
    if st != 200 or r.get('code') != 'BP00000':
        fail.append((name, r.get('code')))
        continue
    d = r.get('data')
    if isinstance(d, dict):
        t = d.get('total')
        n = int(t) if t not in (None, '') else len(d.get('rows') or d.get('widgets') or [])
    elif isinstance(d, list):
        n = len(d)
    else:
        n = 1 if d else 0
    if n:
        okc += 1
    else:
        empty.append(name)

print(' 有数据 %d ｜ 空 %d ｜ 失败 %d ｜ 共 %d'
      % (okc, len(empty), len(fail), len(PAGES)))
if empty:
    print(' 空：%s' % ', '.join(empty))
if fail:
    print(' 失败：%s' % fail)
