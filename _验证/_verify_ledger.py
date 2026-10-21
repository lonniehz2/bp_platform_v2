# -*- coding: utf-8 -*-
"""fin 收尾三表 · 验证（催缴 / 对账 / 资金流水 含自动记账）"""
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


sfx = str(int(time.time()))[-5:]
print('=' * 76)
print(' fin 收尾 · 催缴 / 对账 / 资金流水')
print('=' * 76)

# ---------- 造数据 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'LG-' + sfx, 'orgName': '账务验证小区',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'spaceCode': 'LGB-' + sfx,
                                       'spaceName': '1幢', 'spaceType': 'BUILDING'})
bd = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(bd),
                                       'spaceCode': 'LGU-' + sfx, 'spaceName': '1单元',
                                       'spaceType': 'UNIT'})
un = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(un),
                                       'spaceCode': 'LGF-' + sfx, 'spaceName': '1层',
                                       'spaceType': 'FLOOR'})
fl = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(fl),
                                       'spaceCode': 'LGR-' + sfx, 'spaceName': '101',
                                       'spaceType': 'ROOM', 'area': '90'})
rm = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'LGH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '90'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4001, 'lesseeName': '账务张三',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('造合同', bool(cid), cid)

# 逾期账单
st, r = call('POST', '/api/v1/fin/bills', {
    'feeItemId': 1, 'orgId': int(org), 'contractId': int(cid), 'houseId': int(house),
    'personId': 4001, 'payerName': '账务张三', 'billPeriod': '2026-03',
    'periodStart': '2026-03-01', 'periodEnd': '2026-03-31', 'billAmount': '1000',
    'dueDate': '2026-03-10', 'generateType': 'MANUAL'})
billId = (r.get('data') or {}).get('id')
chk('造逾期账单 1000', bool(billId), billId)

# ==================== 1. 催缴 ====================
st, r = call('GET', '/api/v1/fin/dunnings/scan?minOverdueDays=3&maxDunningTimes=3')
chk('⭐ 催缴建议扫描', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
scan = r.get('data') or []
mine = next((x for x in scan if str(x.get('billId')) == str(billId)), None)
chk('⭐ 扫到本账单', mine is not None, len(scan))
if mine:
    print('     账单 %s 欠费 %s 逾期 %s 天 已催 %s 次'
          % (mine.get('billNo'), mine.get('payableAmount'), mine.get('overdueDays'),
             mine.get('dunningTimes')))
    chk('欠费金额 1000.00', str(mine.get('payableAmount')) == '1000.00',
        mine.get('payableAmount'))
    chk('初始催缴次数 0', str(mine.get('dunningTimes')) == '0', mine.get('dunningTimes'))

# 第一次催缴：短信
st, r = call('POST', '/api/v1/fin/dunnings', {
    'billId': int(billId), 'personId': 4001, 'dunningType': 'SMS',
    'dunningContent': '您的租金已逾期，请尽快缴纳', 'operatorId': 9001})
chk('⭐ 登记催缴（短信）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
d1 = r.get('data') or {}
chk('⭐ 催缴次数自动为 1', str(d1.get('dunningNo')) == '1', d1.get('dunningNo'))
chk('方式标签=短信', d1.get('dunningTypeLabel') == '短信', d1.get('dunningTypeLabel'))

# 第二次：上门（应提示留证）
st, r = call('POST', '/api/v1/fin/dunnings', {
    'billId': int(billId), 'dunningType': 'VISIT',
    'dunningContent': '上门催缴', 'evidenceUrl': 'https://x/visit1.jpg', 'operatorId': 9001})
d2 = r.get('data') or {}
chk('⭐ 第二次催缴次数为 2', str(d2.get('dunningNo')) == '2', d2.get('dunningNo'))
chk('上门佐证已记录', bool(d2.get('evidenceUrl')), d2.get('evidenceUrl'))

st, r = call('GET', '/api/v1/fin/dunnings/by-bill/%s' % billId)
chk('⭐ 按账单查催缴历史', r.get('code') == 'BP00000' and len(r.get('data') or []) == 2,
    len(r.get('data') or []))

# 已缴清账单不可催缴
st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': int(org), 'personId': 4001, 'payerName': '账务张三',
    'payAmount': '1000', 'payChannel': 'WECHAT'})
pid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
     {'billId': int(billId), 'amount': '1000'})
st, r = call('POST', '/api/v1/fin/dunnings', {
    'billId': int(billId), 'dunningType': 'SMS'})
chk('⭐ 已缴清账单不可催缴', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/dunnings', {
    'billId': int(billId), 'dunningType': 'BAD'})
chk('非法催缴方式被拒', r.get('code') == 'BP10001', r.get('code'))

# ==================== 2. ⭐ 资金流水（自动记账）====================
st, r = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=50&bizId=%s&bizType=PAYMENT' % pid)
chk('⭐ 收款自动记流水', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))
rows = (r.get('data') or {}).get('rows') or []
if rows:
    f = rows[0]
    print('     流水 %s 类型 %s 金额 %s' % (f.get('flowNo'), f.get('flowTypeLabel'),
                                          f.get('amount')))
    chk('⭐ 收款流水类型 INCOME/收入', f.get('flowType') == 'INCOME'
        and f.get('flowTypeLabel') == '收入', f.get('flowType'))
    chk('⭐ 金额为正 1000.00', str(f.get('amount')) == '1000.00', f.get('amount'))
    chk('业务类型 PAYMENT', f.get('bizType') == 'PAYMENT', f.get('bizType'))
    chk('单号 FC 开头', str(f.get('flowNo', '')).startswith('FC'), f.get('flowNo'))
    fid = f.get('id')
    st, r = call('POST', '/api/v1/fin/cash-flows/%s/verify' % fid, {'remark': '核对无误'})
    chk('⭐ 校验流水', (r.get('data') or {}).get('verifyStatus') == 'VERIFIED',
        (r.get('data') or {}).get('verifyStatus'))

# 退款自动记流水
st, r = call('POST', '/api/v1/fin/deposits', {
    'contractId': int(cid) + 7, 'personId': 4001, 'depositAmount': '1000',
    'paidAmount': '1000'})
did = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/refunds', {
    'contractId': int(cid) + 7, 'personId': 4001, 'refundAmount': '600',
    'refundType': 'DEPOSIT'})
rid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/fin/refunds/%s/approve' % rid, {'approveById': 9003})
st, r = call('POST', '/api/v1/fin/refunds/%s/complete' % rid, {})
chk('退款打款成功', (r.get('data') or {}).get('refundStatus') == 'SUCCESS', r.get('code'))

st, r = call('GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=20&bizType=REFUND&bizId=%s' % rid)
rr = (r.get('data') or {}).get('rows') or []
chk('⭐ 退款自动记流水', len(rr) >= 1, len(rr))
if rr:
    chk('⭐ 退款为支出且金额为负 -600.00', rr[0].get('flowType') == 'EXPENSE'
        and str(rr[0].get('amount')) == '-600.00',
        (rr[0].get('flowType'), rr[0].get('amount')))

# 手工流水 + 净额
st, r = call('POST', '/api/v1/fin/cash-flows', {
    'flowType': 'ADJUST', 'bizType': 'OTHER', 'amount': '-50', 'remark': '手续费调整'})
chk('手工登记流水', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/fin/cash-flows', {'flowType': 'INCOME', 'amount': '0'})
chk('金额 0 被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('GET', '/api/v1/fin/cash-flows/net')
chk('⭐ 净流入接口', r.get('code') == 'BP00000' and r.get('data') is not None, r.get('data'))
print('     期间净流入：%s' % r.get('data'))

# ==================== 3. 对账 ====================
today = time.strftime('%Y-%m-%d')
st, r = call('POST', '/api/v1/fin/reconciles', {
    'reconcileDate': today, 'reconcileType': 'CHANNEL', 'payChannel': 'WECHAT',
    'channelAmount': '1000'})
chk('⭐ 对账（系统金额自动汇总）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
rc = r.get('data') or {}
rcid = rc.get('id')
print('     系统 %s 渠道 %s 差异 %s 状态 %s'
      % (rc.get('systemAmount'), rc.get('channelAmount'), rc.get('diffAmount'),
         rc.get('reconcileStatusLabel')))
chk('系统金额 ≥ 1000', float(rc.get('systemAmount') or 0) >= 1000.0, rc.get('systemAmount'))
chk('单号 FRC 开头', str(rc.get('reconcileNo', '')).startswith('FRC'), rc.get('reconcileNo'))

# 造差异
st, r = call('POST', '/api/v1/fin/reconciles', {
    'reconcileDate': today, 'reconcileType': 'MANUAL',
    'systemAmount': '5000', 'channelAmount': '4800', 'diffCount': 2})
diff = r.get('data') or {}
diffId = diff.get('id')
chk('⭐ 差异金额 200.00', str(diff.get('diffAmount')) == '200.00', diff.get('diffAmount'))
chk('⭐ 状态 DIFF/有差异', diff.get('reconcileStatus') == 'DIFF'
    and diff.get('reconcileStatusLabel') == '有差异', diff.get('reconcileStatus'))
chk('matched=false', diff.get('matched') in (False, 'false'), diff.get('matched'))

st, r = call('POST', '/api/v1/fin/reconciles/%s/handle' % diffId, {'remark': '渠道手续费差异，已确认'})
chk('⭐ 处理差异 → HANDLED/已处理',
    (r.get('data') or {}).get('reconcileStatus') == 'HANDLED',
    str(r.get('code')) + ' ' + str((r.get('data') or {}).get('reconcileStatus')))
st, r = call('POST', '/api/v1/fin/reconciles/%s/handle' % diffId, {})
chk('⭐ 重复处理被拒', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/fin/reconciles/%s/handle' % rcid, {})
chk('账实相符无需处理', r.get('code') == 'BP40001', r.get('code'))

st, r = call('GET', '/api/v1/fin/reconciles?pageNum=1&pageSize=20')
chk('对账分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 2, (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/reconciles?pageNum=1&pageSize=20&status=DIFF')
chk('按状态筛对账', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/fin/reconciles/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 76)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 76)
