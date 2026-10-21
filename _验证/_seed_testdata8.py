# -*- coding: utf-8 -*-
"""验证 P0 数据流：押金收取→抵扣→退款审批→打款、补贴发放、催缴、年审"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
CONTRACTS = D.get('contracts', [])


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


def ok(r):
    return r.get('code') == 'BP00000'


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# ---------- 1) 押金：收取 → 抵扣 → 退款 ----------
print('— 押金流程 —')
deps = call('GET', '/api/v1/fin/deposits?pageNum=1&pageSize=20').get('data', {}).get('rows') or []
print('  押金台账 %d 条' % len(deps))
if deps:
    d0 = deps[0]
    print('    首条：合同 %s 余额 %s 状态 %s'
          % (d0.get('contractId'), d0.get('balanceAmount'), d0.get('depositStatus')))
    # 抵扣
    r = call('POST', '/api/v1/fin/deposits/%s/deduct' % d0['id'],
             {'amount': 300, 'reason': '墙面损坏赔偿'})
    print('  %s 抵扣 300 → 余额 %s 状态 %s'
          % ('✓' if ok(r) else '✗', (r.get('data') or {}).get('balanceAmount'),
             (r.get('data') or {}).get('depositStatus')))
    # 退款申请（金额必填）
    bal = float((r.get('data') or {}).get('balanceAmount') or 0)
    rr = call('POST', '/api/v1/fin/refunds', {
        'contractId': d0.get('contractId'), 'personId': d0.get('personId'),
        'refundAmount': bal, 'refundType': 'DEPOSIT',
        'refundChannel': 'BANK', 'refundReason': '退租结算'})
    rid = (rr.get('data') or {}).get('id')
    print('  %s 退款申请 %s 元 → id=%s %s' % ('✓' if ok(rr) else '✗', bal, rid,
                                            str(rr.get('message'))[:40]))
    if rid:
        r2 = call('POST', '/api/v1/fin/refunds/%s/approve' % rid, {'approveById': 1001})
        print('  %s 批准 → %s' % ('✓' if ok(r2) else '✗',
                                 (r2.get('data') or {}).get('refundStatus')))
        r3 = call('POST', '/api/v1/fin/refunds/%s/complete' % rid)
        print('  %s 打款完成 → %s' % ('✓' if ok(r3) else '✗',
                                     (r3.get('data') or {}).get('refundStatus')))
        d1 = call('GET', '/api/v1/fin/deposits/%s' % d0['id']).get('data') or {}
        print('    押金最终：已抵扣 %s 已退还 %s 余额 %s 状态 %s'
              % (d1.get('deductAmount'), d1.get('refundAmount'),
                 d1.get('balanceAmount'), d1.get('depositStatus')))

# ---------- 2) 补贴：批量发放 ----------
print('\n— 补贴发放 —')
r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2026-10', 'orgId': ORG, 'payMode': 'OFFSET', 'dryRun': False})
print('  %s 批量发放 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                str(r.get('data') or r.get('message'))[:90]))
subs = call('GET', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=5')
print('  补贴记录：%s 条' % (subs.get('data') or {}).get('total'))

# ---------- 3) 催缴：扫描 + 登记 ----------
print('\n— 催缴 —')
r = call('POST', '/api/v1/fin/dunnings/scan')
print('  %s 扫描生成催缴 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                    str(r.get('data') or r.get('message'))[:70]))
bills = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=3').get('data', {}).get('rows') or []
if bills:
    r = call('POST', '/api/v1/fin/dunnings', {
        'billId': bills[0]['id'], 'personId': bills[0].get('personId'),
        'actionType': 'SMS', 'remark': '测试催缴'})
    print('  %s 登记催缴 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                     str(r.get('message'))[:50]))
    dn = call('GET', '/api/v1/fin/dunnings?pageNum=1&pageSize=5')
    print('  催缴记录：%s 条' % (dn.get('data') or {}).get('total'))

# ---------- 4) 年审：批量发起 ----------
print('\n— 年审 —')
r = call('POST', '/api/v1/annual-reviews/batch', {
    'reviewYear': '2026', 'orgId': ORG, 'reviewBatch': 'AR2026', 'dryRun': False})
print('  %s 批量发起 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                str(r.get('data') or r.get('message'))[:90]))
ar = call('GET', '/api/v1/annual-reviews?pageNum=1&pageSize=5')
print('  年审单：%s 条' % (ar.get('data') or {}).get('total'))

# ---------- 5) 最终指标 ----------
print('\n— 最终指标 —')
m = call('GET', '/api/v1/rpt/metrics/current').get('data') or {}
for k in ('HOUSE_TOTAL', 'HOUSE_OCCUPIED', 'OCCUPANCY_RATE', 'BILL_UNPAID_AMOUNT',
          'PAYMENT_TOTAL_AMOUNT', 'ACCESS_TODAY_COUNT'):
    print('    %-24s %s' % (k, m.get(k)))
