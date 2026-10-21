# -*- coding: utf-8 -*-
"""收款登记 + 核销（打通「出账→收款→核销」闭环）"""
import json
import urllib.error
import urllib.request
from collections import defaultdict

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']


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

# ---------- 1) 取未缴账单 ----------
r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=100&billStatus=UNPAID')
bills = (r.get('data') or {}).get('rows') or []
print('未缴账单：%d 张，合计 %s'
      % (len(bills), sum(float(b.get('payableAmount') or 0) for b in bills)))

by_person = defaultdict(list)
for b in bills:
    by_person[b.get('personId')].append(b)

# ---------- 2) 逐人登记收款 ----------
print('\n— 登记收款 —')
payments = {}
for pid, bl in by_person.items():
    amt = round(sum(float(b.get('payableAmount') or 0) for b in bl), 2)
    r = call('POST', '/api/v1/fin/payments', {
        'orgId': ORG, 'personId': pid, 'payerName': '测试租户',
        'payAmount': amt, 'payChannel': 'BANK',
        'tradeNo': 'TN%d' % (int(pid) % 1000000), 'unknownFlag': 0,
        'remark': '自动测试收款'})
    pd = r.get('data') or {}
    print('  %s person=%s 金额 %s → paymentId=%s %s'
          % ('✓' if r.get('code') == 'BP00000' else '✗', pid, amt,
             pd.get('id'), str(r.get('message'))[:36]))
    if pd.get('id'):
        payments[pid] = pd['id']

# ---------- 3) 核销 ----------
print('\n— 核销 —')
ok = 0
for pid, bl in by_person.items():
    pay_id = payments.get(pid)
    if not pay_id:
        continue
    for b in bl:
        r = call('POST', '/api/v1/fin/payments/%s/allocate' % pay_id,
                 {'billId': b.get('id'), 'amount': b.get('payableAmount')})
        good = r.get('code') == 'BP00000'
        if good:
            ok += 1
        else:
            print('  ✗ bill=%s %s %s' % (b.get('id'), r.get('code'),
                                        str(r.get('message'))[:44]))
print('  核销成功 %d / %d 张' % (ok, len(bills)))

# ---------- 4) 结果核对 ----------
print('\n— 结果 —')
r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=5&billStatus=PAID')
print('  已缴账单数：%s' % (r.get('data') or {}).get('total'))
m = call('GET', '/api/v1/rpt/metrics/current').get('data') or {}
for k in ('BILL_UNPAID_AMOUNT', 'PAYMENT_TOTAL_AMOUNT', 'BILL_UNPAID_COUNT'):
    print('    %-24s %s' % (k, m.get(k)))

# ---------- 5) 资金流水 / 对账 ----------
c1 = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=5')
print('\n  资金流水：%s 条' % (c1.get('data') or {}).get('total'))
c2 = call('GET', '/api/v1/fin/reconciles?pageNum=1&pageSize=5')
print('  对账记录：%s 条' % (c2.get('data') or {}).get('total'))
