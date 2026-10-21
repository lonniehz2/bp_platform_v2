# -*- coding: utf-8 -*-
"""公示（≥7天且已结束）→ 配租单签约（验证 D23 硬校验）"""
import json
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def ok(r):
    return r.get('code') == 'BP00000'


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# 1) 先验证未公示时签约会被拦（D23）
als = (call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10', tok=TOK)
       .get('data', {}).get('rows') or [])
print('配租单 %d 条' % len(als))
if als:
    r = call('POST', '/api/v1/allocation/allocations/%s/sign' % als[0]['id'],
             {}, TOK)
    print('  未公示签约 → %s %s' % (r.get('code'), str(r.get('message'))[:80]))

# 2) 建公示：8 天前开始、昨天结束（满足 ≥7 天且已结束）
today = date.today()
start = (today - timedelta(days=8)).isoformat()
end = (today - timedelta(days=1)).isoformat()
print('\n— 公示（%s ~ %s）—' % (start, end))
r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': ORG,
    'title': '测试配租结果公示', 'startDate': start, 'endDate': end}, TOK)
pid = (r.get('data') or {}).get('id')
print('  %s 创建公示 → %s %s' % ('✓' if ok(r) else '✗', pid,
                              str(r.get('message'))[:56]))

if pid:
    r2 = call('POST', '/api/v1/publicities/%s/publish' % pid, None, TOK)
    print('  %s 发布 → %s %s' % ('✓' if ok(r2) else '✗', r2.get('code'),
                               str(r2.get('message'))[:44]))
    r3 = call('POST', '/api/v1/publicities/%s/close' % pid, {'remark': '公示期满'},
              TOK)
    print('  %s 结束公示 → %s %s' % ('✓' if ok(r3) else '✗', r3.get('code'),
                                  str(r3.get('message'))[:44]))

# 3) 公示完成校验
r = call('GET', '/api/v1/publicities/allocation-check?orgId=%s' % ORG, None, TOK)
print('  完成校验：%s %s' % (r.get('code'), str(r.get('data'))[:40]))

# 4) 签约
print('\n— 配租单签约 —')
for a in als[:3]:
    r = call('POST', '/api/v1/allocation/allocations/%s/sign' % a['id'], {}, TOK)
    print('  %s %s → %s %s' % ('✓' if ok(r) else '✗', a.get('allocationNo'),
                              r.get('code'),
                              (r.get('data') or {}).get('allocationStatus')
                              or str(r.get('message'))[:60]))

als2 = (call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10', tok=TOK)
        .get('data', {}).get('rows') or [])
print('\n签约后状态：')
for x in als2[:5]:
    print('  %s %s' % (x.get('allocationNo'), x.get('allocationStatus')))

# 5) 最终看板
m = call('GET', '/api/v1/rpt/metrics/current', tok=TOK).get('data') or {}
print('\n— 最终指标 —')
for k in ('HOUSE_TOTAL', 'HOUSE_OCCUPIED', 'OCCUPANCY_RATE', 'BILL_UNPAID_AMOUNT',
          'PAYMENT_TOTAL_AMOUNT', 'ACCESS_TODAY_COUNT', 'ACCESS_ABNORMAL_COUNT'):
    print('    %-22s %s' % (k, m.get(k)))
