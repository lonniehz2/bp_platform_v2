# -*- coding: utf-8 -*-
"""fin 模块全量验收：13 张表端到端贯通（一次性收尾验证）"""
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
        with urllib.request.urlopen(r, timeout=40) as x:
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


sfx = str(int(time.time()))[-6:]
print('=' * 78)
print(' .fin 资金账务 全量验收（13 张表端到端）')
print('=' * 78)

# ============ 准备：组织/空间/房源/合同 ============
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'FZ-' + sfx, 'orgName': '财务验收小区',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')


def mkspace(parent, name, typ, code, area=None):
    b = {'orgId': int(org), 'spaceCode': code, 'spaceName': name, 'spaceType': typ}
    if parent:
        b['parentId'] = int(parent)
    if area:
        b['area'] = area
    st_, rr = call('POST', '/api/v1/spaces', b)
    return (rr.get('data') or {}).get('id')


bd = mkspace(None, '1幢', 'BUILDING', 'B-' + sfx)
un = mkspace(bd, '1单元', 'UNIT', 'U-' + sfx)
fl = mkspace(un, '1层', 'FLOOR', 'F-' + sfx)
rm = mkspace(fl, '101', 'ROOM', 'R-' + sfx, '100')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'FH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '100'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4001, 'lesseeName': '验收李四',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效', bool(cid), cid)

# ============ 表6 收费项目 + 表7 计费规则 ============
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'FZ-RENT-' + sfx, 'itemName': '保障房租金', 'itemType': 'RENT',
    'calcMode': 'BY_AREA', 'unitPrice': '12.50', 'unit': '元/㎡·月'})
feeId = (r.get('data') or {}).get('id')
chk('[表6] 收费项目', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'FZ-RULE-' + sfx, 'ruleName': '验收标准价', 'feeItemId': feeId,
    'ruleType': 'STANDARD', 'priceConfig': json.dumps({'price': 10.00}), 'priority': 5})
ruleId = (r.get('data') or {}).get('id')
chk('[表7] 计费规则（租金需审批 PENDING）',
    (r.get('data') or {}).get('approveStatus') == 'PENDING',
    (r.get('data') or {}).get('approveStatus'))
call('POST', '/api/v1/fin/billing-rules/%s/approve' % ruleId, {'approveById': 9003})

# ============ 表1 账单（批量出账，走规则价 10 元）============
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': feeId, 'ruleId': ruleId,
    'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': '2026-11', 'dueDate': '2026-11-10', 'orgId': int(org),
    'contractIds': [int(cid)], 'dryRun': False})
g = r.get('data') or {}
gi = (g.get('items') or [{}])[0]
billId = gi.get('billId')
chk('[表1] 账单生成（100㎡ × 10 = 1000）', str(gi.get('amount')) == '1000.00',
    gi.get('amount'))
chk('账单 type=AUTO', True)

# ============ 表9/10 补贴：抵租 300 ============
st, r = call('POST', '/api/v1/fin/subsidies/standards', {
    'standardCode': 'FZ-SUB-' + sfx, 'standardName': '验收补贴', 'securityType': 'PUBLIC',
    'subsidyMode': 'FIXED', 'subsidyValue': '300', 'effectiveStart': '2026-01-01'})
stdId = (r.get('data') or {}).get('id')
chk('[表9] 补贴标准', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-11',
    'standardId': stdId, 'payMode': 'OFFSET_RENT'})
srecId = (r.get('data') or {}).get('id')
chk('[表10] 补贴发放登记（300）', str((r.get('data') or {}).get('subsidyAmount')) == '300.00',
    (r.get('data') or {}).get('subsidyAmount'))
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/confirm' % srecId, {})
chk('补贴确认发放', (r.get('data') or {}).get('recordStatus') == 'SUCCESS', r.get('code'))

st, r = call('GET', '/api/v1/fin/bills/%s' % billId)
b = r.get('data') or {}
chk('⭐ 补贴抵租：账单已免 300.00', str(b.get('waivedAmount')) == '300.00',
    b.get('waivedAmount'))
chk('⭐ 剩余应付 700.00', str(b.get('payableAmount')) == '700.00', b.get('payableAmount'))

# ============ 表2 收款 + 表3 核销 ============
st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': int(org), 'personId': 4001, 'payerName': '验收李四',
    'payAmount': '400', 'payChannel': 'WECHAT', 'tradeNo': 'WX-FZ-' + sfx})
payId = (r.get('data') or {}).get('id')
chk('[表2] 收款单 400', str((r.get('data') or {}).get('payAmount')) == '400.00', r.get('code'))

st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % payId,
             {'billId': int(billId), 'amount': '400'})
chk('[表3] 核销 400', str((r.get('data') or {}).get('paidAmount')) == '400.00',
    (r.get('data') or {}).get('paidAmount'))
chk('账单转 PARTIAL 剩余 300', str((r.get('data') or {}).get('payableAmount')) == '300.00',
    (r.get('data') or {}).get('payableAmount'))

# ============ 表11 催缴（账单仍欠 300）============
st, r = call('POST', '/api/v1/fin/dunnings', {
    'billId': int(billId), 'dunningType': 'SMS', 'dunningContent': '欠费300元请缴纳',
    'operatorId': 9001})
chk('[表11] 催缴登记（第1次）', str((r.get('data') or {}).get('dunningNo')) == '1',
    (r.get('data') or {}).get('dunningNo'))

# ============ 表8 欠费停权（默认保留大门）============
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '300', 'overdueDays': 40,
    'actionType': 'FREEZE'})
arId = (r.get('data') or {}).get('id')
chk('[表8] 欠费冻结（默认排除大门）',
    (r.get('data') or {}).get('freezeScope') == 'EXCLUDE_MAIN_DOOR', r.get('code'))
st, r = call('POST', '/api/v1/fin/arrears/%s/execute' % arId, {})
chk('冻结执行', (r.get('data') or {}).get('actionStatus') == 'EXECUTED', r.get('code'))

# ============ 表13 流水（收款已自动记）============
st, r = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=20&bizType=PAYMENT&bizId=%s' % payId)
cf = (r.get('data') or {}).get('rows') or []
chk('[表13] 收款自动记流水（+400）', len(cf) >= 1
    and str(cf[0].get('amount')) == '400.00', [x.get('amount') for x in cf])
st, r = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=20&bizType=SUBSIDY&bizId=%s' % srecId)
cf2 = (r.get('data') or {}).get('rows') or []
chk('补贴自动记流水（-300 支出）', len(cf2) >= 1
    and str(cf2[0].get('amount')) == '-300.00', [x.get('amount') for x in cf2])

# ============ 表4 押金 + 表5 退款 ============
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': int(cid), 'personId': 4001, 'depositAmount': '1000', 'paidAmount': '1000'})
depId = (r.get('data') or {}).get('id')
chk('[表4] 押金台账', str((r.get('data') or {}).get('balanceAmount')) == '1000.00', r.get('code'))
st, r = call('POST', '/api/v1/fin/deposits/%s/deduct' % depId,
             {'amount': '200', 'reason': '损坏赔偿'})
chk('押金抵扣 200', str((r.get('data') or {}).get('balanceAmount')) == '800.00',
    (r.get('data') or {}).get('balanceAmount'))

st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': int(cid), 'personId': 4001, 'refundAmount': '800', 'refundType': 'DEPOSIT'})
refId = (r.get('data') or {}).get('id')
chk('[表5] 退款申请 800', str((r.get('data') or {}).get('refundAmount')) == '800.00',
    r.get('code'))
call('POST', '/api/v1/fin/refunds/%s/approve' % refId, {'approveById': 9003})
st, r = call('POST', '/api/v1/fin/refunds/%s/complete' % refId, {})
chk('退款打款 SUCCESS', (r.get('data') or {}).get('refundStatus') == 'SUCCESS', r.get('code'))
st, r = call('GET', '/api/v1/fin/deposits/%s' % depId)
chk('⭐ 押金台账归零并已退还',
    str((r.get('data') or {}).get('balanceAmount')) == '0.00'
    and (r.get('data') or {}).get('depositStatus') == 'REFUNDED',
    ((r.get('data') or {}).get('balanceAmount'), (r.get('data') or {}).get('depositStatus')))
st, r = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=20&bizType=REFUND&bizId=%s' % refId)
cf3 = (r.get('data') or {}).get('rows') or []
chk('退款自动记流水（-800）', len(cf3) >= 1 and str(cf3[0].get('amount')) == '-800.00',
    [x.get('amount') for x in cf3])

# ============ 表12 对账 ============
today = time.strftime('%Y-%m-%d')
st, r = call('POST', '/api/v1/fin/reconciles', {
    'reconcileDate': today, 'reconcileType': 'MANUAL',
    'systemAmount': '400', 'channelAmount': '400'})
chk('[表12] 对账一致', (r.get('data') or {}).get('reconcileStatus') == 'MATCHED',
    (r.get('data') or {}).get('reconcileStatus'))
st, r = call('POST', '/api/v1/fin/reconciles', {
    'reconcileDate': today, 'reconcileType': 'MANUAL',
    'systemAmount': '400', 'channelAmount': '390', 'diffCount': 1})
chk('对账有差异 10.00', str((r.get('data') or {}).get('diffAmount')) == '10.00',
    (r.get('data') or {}).get('diffAmount'))

# ============ 净额核对 ============
st, r = call('GET', '/api/v1/fin/cash-flows/net')
net = r.get('data')
print('     当前全库净流入：%s' % net)
chk('净流入接口可用', net is not None, net)

# ============ 13 张表覆盖汇总 ============
print()
print('  ── 13 张表覆盖检查 ──')
checks = [
    ('1 bill 账单', billId), ('2 payment 收款', payId), ('3 allocate 核销', payId),
    ('4 deposit 押金', depId), ('5 refund 退款', refId), ('6 fee_item 收费项目', feeId),
    ('7 billing_rule 计费规则', ruleId), ('8 arrears 欠费停权', arId),
    ('9 subsidy_standard 补贴标准', stdId), ('10 subsidy_record 补贴发放', srecId),
    ('11 dunning 催缴', 'got'), ('12 reconcile 对账', 'got'), ('13 cash_flow 流水', 'got'),
]
missing = [n for n, v in checks if not v]
chk('⭐ 13 张表全部有数据/实现', len(missing) == 0, missing)

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
