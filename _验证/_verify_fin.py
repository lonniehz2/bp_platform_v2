# -*- coding: utf-8 -*-
"""fin 账单与收款核销 · 真实接口验证"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
H = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600', 'X-User-Id': '1001'}


def call(m, p, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=25) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


ok = fail = 0


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


print('=' * 72)
print(' 资金账务 · 账单与收款核销验证')
print('=' * 72)


def mkBill(amount='1000', discount='0', late='0', due='2026-12-31'):
    return call('POST', '/api/v1/fin/bills', {
        'feeItemId': 1, 'orgId': 7001, 'contractId': 2001, 'houseId': 5001,
        'personId': 4001, 'payerName': '张三', 'payerPhone': '13800138000',
        'billPeriod': '2026-10', 'periodStart': '2026-10-01', 'periodEnd': '2026-10-31',
        'billAmount': amount, 'discountAmount': discount, 'lateFee': late,
        'dueDate': due, 'generateType': 'MANUAL', 'remark': '10月租金'})


# 1. 生成账单
st, r = mkBill()
chk('生成账单', r.get('code') == 'BP00000', str(r.get('code')) + ' ' + str(r.get('message')))
b = r.get('data') or {}
bid = b.get('id')
chk('状态 UNPAID/未缴', b.get('billStatus') == 'UNPAID' and b.get('billStatusLabel') == '未缴',
    b.get('billStatus'))
chk('单号 FB 开头', str(b.get('billNo', '')).startswith('FB'), b.get('billNo'))
chk('⭐ 应付 = 应收 1000.00', str(b.get('payableAmount')) == '1000.00', b.get('payableAmount'))
chk('已收/已免为 0', str(b.get('paidAmount')) == '0.00' and str(b.get('waivedAmount')) == '0.00',
    (b.get('paidAmount'), b.get('waivedAmount')))

# 2. 应付计算：应收 - 减免 + 滞纳金
st, r = mkBill('1000', '100', '50')
c = r.get('data') or {}
chk('⭐ 应付 = 1000-100+50 = 950.00', str(c.get('payableAmount')) == '950.00',
    c.get('payableAmount'))
cid = c.get('id')

st, r = mkBill('1000', '1200')
chk('减免超应收被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/fin/bills', {
    'feeItemId': 1, 'orgId': 7001, 'periodStart': '2026-10-31', 'periodEnd': '2026-10-01',
    'billAmount': '100'})
chk('截止日早于起始日被拒', r.get('code') == 'BP10001', r.get('code'))

# 3. 收款单
st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': 7001, 'personId': 4001, 'payerName': '张三', 'payAmount': '600',
    'payChannel': 'WECHAT', 'tradeNo': 'WX123456'})
chk('登记收款', r.get('code') == 'BP00000', r.get('code'))
p = r.get('data') or {}
pid = p.get('id')
chk('状态 SUCCESS/成功', p.get('payStatus') == 'SUCCESS' and p.get('payStatusLabel') == '成功',
    p.get('payStatus'))
chk('单号 FP 开头', str(p.get('paymentNo', '')).startswith('FP'), p.get('paymentNo'))
chk('核销状态 UNRECONCILED', p.get('reconcileStatus') == 'UNRECONCILED', p.get('reconcileStatus'))
chk('⭐ 可核销余额 = 600.00', str(p.get('remainAmount')) == '600.00', p.get('remainAmount'))

st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': 7001, 'personId': 4001, 'payAmount': '0', 'payChannel': 'CASH'})
chk('收款金额必须 > 0', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': 7001, 'payAmount': '100', 'payChannel': 'BAD'})
chk('非法渠道被拒', r.get('code') == 'BP10001', r.get('code'))

# 4. 核销：部分核销
st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
             {'billId': bid, 'amount': '400'})
al = r.get('data') or {}
chk('⭐ 部分核销 400', r.get('code') == 'BP00000'
    and str(al.get('paidAmount')) == '400.00', (r.get('code'), al.get('paidAmount')))
chk('账单状态 → PARTIAL/部分缴', al.get('billStatus') == 'PARTIAL'
    and al.get('billStatusLabel') == '部分缴', al.get('billStatus'))
chk('账单剩余应付 600.00', str(al.get('payableAmount')) == '600.00', al.get('payableAmount'))

st, r = call('GET', '/api/v1/fin/payments/%s' % pid)
pv = r.get('data') or {}
chk('⭐ 收款单已核销 400.00', str(pv.get('reconciledAmount')) == '400.00',
    pv.get('reconciledAmount'))
chk('收款单核销状态 PARTIAL', pv.get('reconcileStatus') == 'PARTIAL', pv.get('reconcileStatus'))
chk('可核销余额降至 200.00', str(pv.get('remainAmount')) == '200.00', pv.get('remainAmount'))

# 5. 核销上限
st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
             {'billId': bid, 'amount': '300'})
chk('⭐ 超收款余额被拒', r.get('code') == 'BP10001'
    and '余额' in str(r.get('message')), str(r.get('message')))

# 6. 收满：核销剩余 200 → 账单变 PAID
st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
             {'billId': bid, 'amount': '200'})
chk('⭐ 收满 → 账单 PAID', (r.get('data') or {}).get('billStatus') == 'PAID',
    (r.get('data') or {}).get('billStatus'))
chk('剩余应付 0.00', str((r.get('data') or {}).get('payableAmount')) == '0.00',
    (r.get('data') or {}).get('payableAmount'))
st, r = call('GET', '/api/v1/fin/payments/%s' % pid)
chk('⭐ 收款单核销状态 RECONCILED',
    (r.get('data') or {}).get('reconcileStatus') == 'RECONCILED',
    (r.get('data') or {}).get('reconcileStatus'))
st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
             {'billId': bid, 'amount': '10'})
chk('已缴账单不可再核销', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/fin/bills/%s/cancel' % bid, {'reason': 'x'})
chk('⭐ 已收款账单不可作废', r.get('code') == 'BP40001', r.get('code'))

# 7. 减免
st, r = call('POST', '/api/v1/fin/bills/%s/waive' % cid,
             {'waiveAmount': '200', 'reason': '困难减免'})
w = r.get('data') or {}
chk('⭐ 减免 200 → 应付 750.00', str(w.get('payableAmount')) == '750.00', w.get('payableAmount'))
chk('已免金额 200.00', str(w.get('waivedAmount')) == '200.00', w.get('waivedAmount'))
st, r = call('POST', '/api/v1/fin/bills/%s/waive' % cid,
             {'waiveAmount': '9999', 'reason': 'x'})
chk('减免超应付被拒', r.get('code') == 'BP10001', r.get('code'))

# 8. 作废（未收款账单）
st, r = mkBill('500')
did = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/bills/%s/cancel' % did, {'reason': '重复开单'})
chk('未收款账单可作废 → CANCELLED',
    (r.get('data') or {}).get('billStatus') == 'CANCELLED',
    (r.get('data') or {}).get('billStatus'))

# 9. 逾期扫描
st, r = mkBill('300', due='2026-01-01')
ovid = (r.get('data') or {}).get('id')
st, r = call('GET', '/api/v1/fin/bills/%s' % ovid)
before = r.get('data') or {}
chk('⭐ 过期账单 overdueNow=true', before.get('overdueNow') in (True, 'true'),
    before.get('overdueNow'))
st, r = call('POST', '/api/v1/fin/bills/scan-overdue')
chk('逾期扫描接口', r.get('code') == 'BP00000' and int(r.get('data') or 0) >= 1, r.get('data'))
st, r = call('GET', '/api/v1/fin/bills/%s' % ovid)
after = r.get('data') or {}
chk('⭐ 扫描后状态 OVERDUE', after.get('billStatus') == 'OVERDUE', after.get('billStatus'))
chk('逾期天数已回填 > 0', int(after.get('overdueDays') or 0) > 0, after.get('overdueDays'))

# 10. 查询
st, r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=20')
chk('账单分页', r.get('code') == 'BP00000' and int((r.get('data') or {}).get('total', 0)) >= 3,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=20&status=PAID')
chk('按状态筛选', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/fin/payments?pageNum=1&pageSize=20')
chk('收款分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/fin/bills/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 72)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 72)
