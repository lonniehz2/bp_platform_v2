# -*- coding: utf-8 -*-
"""走完合同状态机：submit-sign → start-signing → sign，然后出账"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
CONTRACTS = D.get('contracts', [])
FEE = D.get('feeItems', [])


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
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


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

print('— 合同状态机 —')
ok_cnt = 0
for c in CONTRACTS:
    cid = c['id']
    r1 = call('POST', '/api/v1/contracts/%s/submit-sign' % cid)
    r2 = call('POST', '/api/v1/contracts/%s/start-signing' % cid, {'signVendor': 'PAPER'})
    r3 = call('POST', '/api/v1/contracts/%s/sign' % cid,
              {'signVendor': 'PAPER', 'reason': '测试数据'})
    st = (r3.get('data') or {}).get('contractStatus')
    good = r3.get('code') == 'BP00000'
    if good:
        ok_cnt += 1
    print('  %s %s → %s' % ('✓' if good else '✗', cid,
                           st or (str(r1.get('code')) + '/' + str(r2.get('code')) +
                                  '/' + str(r3.get('code')) + ' ' +
                                  str(r3.get('message'))[:40])))
print('  履约中 %d / %d' % (ok_cnt, len(CONTRACTS)))

print('\n— 出账 —')
for fid in FEE:
    r = call('POST', '/api/v1/fin/bills/generate', {
        'orgId': ORG, 'feeItemId': fid,
        'periodStart': '2026-10-01', 'periodEnd': '2026-10-31', 'dryRun': False})
    d = r.get('data') or {}
    print('  %s feeItem=%s 合同%d 生成%d 金额%s'
          % ('✓' if r.get('code') == 'BP00000' else '✗', fid,
             d.get('totalContracts', 0), d.get('generated', 0), d.get('totalAmount', '0')))

print('\n— 账单核对 —')
b = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=5')
rows = (b.get('data') or {}).get('rows') or []
print('  账单总数：%s' % (b.get('data') or {}).get('total'))
for x in rows[:3]:
    print('    %s %s 待缴 %s 状态 %s' % (x.get('billNo'), x.get('billPeriod'),
                                       x.get('payableAmount'), x.get('billStatus')))

print('\n— 驾驶舱指标 —')
m = call('GET', '/api/v1/rpt/metrics/current')
md = m.get('data') or {}
for k in ('HOUSE_TOTAL', 'HOUSE_OCCUPIED', 'OCCUPANCY_RATE', 'BILL_UNPAID_AMOUNT',
          'PAYMENT_TOTAL_AMOUNT'):
    print('    %-24s %s' % (k, md.get(k)))
