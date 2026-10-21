# -*- coding: utf-8 -*-
"""押金台账 + 退款单 · 真实接口验证（退租结算全链路）"""
import json
import time
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


sfx = str(int(time.time()))[-5:]
CID = int('92' + sfx)
print('=' * 72)
print(' 押金台账 + 退款 · 退租结算全链路验证')
print('=' * 72)

# 1. 建立押金台账（应收 2000，已收 2000，成都上限 1000 → 超限标记）
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': CID, 'personId': 4001, 'depositAmount': '2000',
    'paidAmount': '2000', 'capAmount': '1000'})
chk('建立押金台账', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
d = r.get('data') or {}
did = d.get('id')
chk('状态 HELD/已收取', d.get('depositStatus') == 'HELD' and d.get('depositStatusLabel') == '已收取',
    d.get('depositStatus'))
chk('⭐ 押金余额 2000.00', str(d.get('balanceAmount')) == '2000.00', d.get('balanceAmount'))
chk('尚欠收 0.00', str(d.get('unpaidAmount')) == '0.00', d.get('unpaidAmount'))
chk('⭐ 超政策上限标记 overCap=true（成都 1000 元）', d.get('overCap') in (True, 'true'),
    d.get('overCap'))

st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': CID, 'personId': 4001, 'depositAmount': '1000'})
chk('⭐ 同合同重复建台账被拒 BP40001', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 2. 押金抵扣（退租损坏赔偿 300）
st, r = call('POST', '/api/v1/fin/deposits/%s/deduct' % did,
             {'amount': '300', 'reason': '墙面损坏赔偿'})
dd = r.get('data') or {}
chk('⭐ 抵扣 300 → 余额 1700.00', str(dd.get('balanceAmount')) == '1700.00',
    dd.get('balanceAmount'))
chk('已抵扣 300.00', str(dd.get('deductAmount')) == '300.00', dd.get('deductAmount'))

st, r = call('POST', '/api/v1/fin/deposits/%s/deduct' % did,
             {'amount': '99999', 'reason': '超额'})
chk('⭐ 抵扣超余额被拒 BP10001', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 3. 申请押金退还（1700）
st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': CID, 'personId': 4001, 'refundAmount': '1700',
    'refundType': 'DEPOSIT', 'refundChannel': 'ORIGINAL',
    'refundReason': '退租退还押金'})
chk('申请押金退还', r.get('code') == 'BP00000', r.get('code'))
rf = r.get('data') or {}
rid = rf.get('id')
chk('状态 PENDING/待审批', rf.get('refundStatus') == 'PENDING'
    and rf.get('refundStatusLabel') == '待审批', rf.get('refundStatus'))
chk('单号 FR 开头', str(rf.get('refundNo', '')).startswith('FR'), rf.get('refundNo'))

st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': CID, 'personId': 4001, 'refundAmount': '9999',
    'refundType': 'DEPOSIT'})
chk('⭐ 退款超押金余额被拒 BP10001', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': 99999, 'personId': 4001, 'refundAmount': '100',
    'refundType': 'DEPOSIT'})
chk('无押金台账不可退押金', r.get('code') == 'BP40001', r.get('code'))

st, r = call('POST', '/api/v1/fin/refunds', {
    'personId': 4001, 'refundAmount': '0', 'refundType': 'OVERPAY'})
chk('退款金额必须 > 0', r.get('code') == 'BP10001', r.get('code'))

# 4. 状态机跳步
st, r = call('POST', '/api/v1/fin/refunds/%s/complete' % rid, {})
chk('⭐ PENDING 直接打款被拒 BP40001', r.get('code') == 'BP40001', r.get('code'))

# 5. 审批 → 打款
st, r = call('POST', '/api/v1/fin/refunds/%s/approve' % rid, {'approveById': 9003})
chk('审批 → APPROVED/已批准', (r.get('data') or {}).get('refundStatus') == 'APPROVED',
    r.get('code'))
st, r = call('POST', '/api/v1/fin/refunds/%s/complete' % rid, {})
cm = r.get('data') or {}
chk('⭐ 打款完成 → SUCCESS/已退款', cm.get('refundStatus') == 'SUCCESS'
    and cm.get('refundStatusLabel') == '已退款', cm.get('refundStatus'))
chk('退款时间已记录', bool(cm.get('refundTime')), cm.get('refundTime'))

# 6. 台账联动：已退 1700，余额应为 0，状态 REFUNDED
st, r = call('GET', '/api/v1/fin/deposits/%s' % did)
dep = r.get('data') or {}
chk('⭐ 台账已退 1700.00', str(dep.get('refundAmount')) == '1700.00',
    dep.get('refundAmount'))
chk('⭐ 台账余额归零 0.00', str(dep.get('balanceAmount')) == '0.00',
    dep.get('balanceAmount'))
chk('⭐ 台账状态 REFUNDED/已退还', dep.get('depositStatus') == 'REFUNDED'
    and dep.get('depositStatusLabel') == '已退还', dep.get('depositStatus'))

st, r = call('POST', '/api/v1/fin/deposits/%s/deduct' % did,
             {'amount': '1', 'reason': 'x'})
chk('已退还台账不可再抵扣', r.get('code') == 'BP40001', r.get('code'))

# 7. 部分退还
CID2 = CID + 1
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': CID2, 'personId': 4002, 'depositAmount': '1000', 'paidAmount': '1000'})
did2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': CID2, 'personId': 4002, 'refundAmount': '400', 'refundType': 'DEPOSIT'})
rid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/fin/refunds/%s/approve' % rid2, {'approveById': 9003})
call('POST', '/api/v1/fin/refunds/%s/complete' % rid2, {})
st, r = call('GET', '/api/v1/fin/deposits/%s' % did2)
p2 = r.get('data') or {}
chk('⭐ 部分退还 → 余额 600.00', str(p2.get('balanceAmount')) == '600.00',
    p2.get('balanceAmount'))
chk('⭐ 状态 PARTIAL_REFUND/部分退还', p2.get('depositStatus') == 'PARTIAL_REFUND',
    p2.get('depositStatus'))

# 8. 驳回
CID3 = CID + 2
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': CID3, 'personId': 4003, 'depositAmount': '500', 'paidAmount': '500'})
st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': CID3, 'personId': 4003, 'refundAmount': '500', 'refundType': 'DEPOSIT'})
rid3 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/refunds/%s/reject' % rid3,
             {'approveById': 9003, 'reason': '账户信息有误'})
chk('驳回 → REJECTED', (r.get('data') or {}).get('refundStatus') == 'REJECTED', r.get('code'))
st, r = call('POST', '/api/v1/fin/refunds/%s/approve' % rid3, {'approveById': 9003})
chk('⭐ REJECTED 终态不可再审批', r.get('code') == 'BP40001', r.get('code'))

# 9. 免收押金（廉租）
CID4 = CID + 3
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': CID4, 'personId': 4004, 'depositAmount': '1000',
    'paidAmount': '1000', 'isExempt': 1, 'exemptReason': '廉租标准免收押金'})
ex = r.get('data') or {}
chk('⭐ 免收押金：应收归零', str(ex.get('depositAmount')) == '0.00', ex.get('depositAmount'))
chk('免收标记', ex.get('exempt') in (True, 'true'), ex.get('exempt'))
chk('免收原因已记录', ex.get('exemptReason') == '廉租标准免收押金', ex.get('exemptReason'))

# 10. 查询
st, r = call('GET', '/api/v1/fin/deposits?pageNum=1&pageSize=20')
chk('押金台账分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 4, (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/deposits/by-contract/%s' % CID)
chk('按合同查台账', r.get('code') == 'BP00000'
    and (r.get('data') or {}).get('contractId') == str(CID), r.get('code'))
st, r = call('GET', '/api/v1/fin/refunds?pageNum=1&pageSize=20')
chk('退款单分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 3, (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/refunds?pageNum=1&pageSize=20&status=SUCCESS')
chk('按状态筛退款', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/fin/deposits/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 72)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 72)
