# -*- coding: utf-8 -*-
"""合同变更验证：年审 ADJUST → 调租 → 写回合同 → 影响出账"""
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
print(' 合同变更 · 年审调租落地验证')
print('=' * 78)

# ---------- 准备 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'CG-' + sfx, 'orgName': '变更验证小区',
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
rm = mkspace(fl, '101', 'ROOM', 'R-' + sfx, '80')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'CGH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 9001, 'lesseeName': '变更王五',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效（月租 1000）', bool(cid), cid)
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('初始月租 1000.00', str((r.get('data') or {}).get('monthlyRent')) == '1000.00',
    (r.get('data') or {}).get('monthlyRent'))

# ---------- 1. ⭐ 调租变更：发起 → 批准 → 写回合同 ----------
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'RENT_ADJUST', 'changeReason': '家庭收入超标，租金由 60% 调为 80%',
    'newMonthlyRent': '1300'})
chk('发起调租变更', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
chg = r.get('data') or {}
chgId = chg.get('id')
chk('类型标签=租金调整', chg.get('changeTypeLabel') == '租金调整', chg.get('changeTypeLabel'))
chk('状态 PENDING/待审批', chg.get('approveStatus') == 'PENDING'
    and chg.get('approveStatusLabel') == '待审批', chg.get('approveStatus'))
chk('⭐ 变更前快照已存', '1000' in str(chg.get('beforeJson')), chg.get('beforeJson'))
chk('⭐ 变更后快照已存', '1300' in str(chg.get('afterJson')), chg.get('afterJson'))

# 同一合同不可有多个待审批
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'PERIOD', 'newLeaseEnd': '2028-12-31'})
chk('⭐ 已有待审批变更 → 拒绝', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 批准前合同租金未变
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐ 批准前合同租金仍 1000.00',
    str((r.get('data') or {}).get('monthlyRent')) == '1000.00',
    (r.get('data') or {}).get('monthlyRent'))

st, r = call('POST', '/api/v1/contract-changes/%s/approve' % chgId, {})
chk('⭐ 批准变更 → APPROVED/已批准',
    (r.get('data') or {}).get('approveStatus') == 'APPROVED', r.get('code'))

st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐⭐ 合同租金已真正写回 1300.00',
    str((r.get('data') or {}).get('monthlyRent')) == '1300.00',
    (r.get('data') or {}).get('monthlyRent'))

st, r = call('POST', '/api/v1/contract-changes/%s/approve' % chgId, {})
chk('⭐ 重复批准被拒', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/contract-changes/%s/reject' % chgId, {'reason': 'x'})
chk('⭐ 已批准不可驳回', r.get('code') == 'BP40001', r.get('code'))

# ---------- 2. 租期变更 ----------
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'PERIOD', 'changeReason': '延长租期一年', 'newLeaseEnd': '2028-12-31'})
chg2 = (r.get('data') or {}).get('id')
chk('发起租期变更', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/contract-changes/%s/approve' % chg2, {})
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐ 止租日已写回 2028-12-31',
    (r.get('data') or {}).get('leaseEnd') == '2028-12-31',
    (r.get('data') or {}).get('leaseEnd'))

# ---------- 3. 驳回 ----------
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'RENT_ADJUST', 'newMonthlyRent': '2000', 'changeReason': '临时加价'})
chg3 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contract-changes/%s/reject' % chg3, {'reason': '无政策依据'})
chk('驳回变更 → REJECTED', (r.get('data') or {}).get('approveStatus') == 'REJECTED',
    r.get('code'))
chk('驳回原因已记录', '无政策依据' in str((r.get('data') or {}).get('changeReason')),
    (r.get('data') or {}).get('changeReason'))
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐ 驳回后合同租金未变（仍 1300）',
    str((r.get('data') or {}).get('monthlyRent')) == '1300.00',
    (r.get('data') or {}).get('monthlyRent'))

# ---------- 4. ⭐⭐ 年审 ADJUST → 调租（端到端）----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': 9001, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL'})
rid = (r.get('data') or {}).get('id')
chk('创建年审单', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/annual-reviews/%s/start' % rid, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {
    'reviewResult': 'ADJUST',
    'checkResult': json.dumps({'income': 9000, 'limit': 6000}),
    'adjustContent': '收入超标，租金上浮至 1500'})
chk('年审完成（ADJUST）',
    (r.get('data') or {}).get('reviewResult') == 'ADJUST', r.get('code'))

st, r = call('POST', '/api/v1/annual-reviews/%s/rent-change' % rid, {
    'newMonthlyRent': '1500', 'reason': '年审收入超标调租'})
chk('⭐⭐ 年审结论 → 发起调租变更', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
chg4 = (r.get('data') or {}).get('id')
chk('变更原因为年审来源', '年审' in str((r.get('data') or {}).get('changeReason')),
    (r.get('data') or {}).get('changeReason'))

st, r = call('POST', '/api/v1/contract-changes/%s/approve' % chg4, {})
chk('批准年审调租', (r.get('data') or {}).get('approveStatus') == 'APPROVED', r.get('code'))
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐⭐ 合同租金最终为 1500.00',
    str((r.get('data') or {}).get('monthlyRent')) == '1500.00',
    (r.get('data') or {}).get('monthlyRent'))

# ---------- 5. 年审非 ADJUST 不可发起调租 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': 9002, 'contractId': int(cid), 'reviewYear': '2027', 'reviewType': 'ANNUAL'})
# 同合同另一人 → 实际会被幂等拦住（同人同年度），这里换类型
if r.get('code') != 'BP00000':
    st, r = call('POST', '/api/v1/annual-reviews', {
        'personId': 9001, 'contractId': int(cid), 'reviewYear': '2028',
        'reviewType': 'SPECIAL'})
rid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid2, {})
call('POST', '/api/v1/annual-reviews/%s/finish' % rid2, {'reviewResult': 'KEEP'})
st, r = call('POST', '/api/v1/annual-reviews/%s/rent-change' % rid2, {'newMonthlyRent': '999'})
chk('⭐ 年审结论非 ADJUST 不可发起调租', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 6. 校验 ----------
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'RENT_ADJUST', 'newMonthlyRent': '1500'})
chk('⭐ 新租金与当前相同被拒', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'RENT_ADJUST'})
chk('调租缺新租金被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'PERIOD'})
chk('租期变更缺止租日被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {
    'changeType': 'PERIOD', 'newLeaseEnd': '2025-01-01'})
chk('新止租日早于起租日被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid, {'changeType': 'BAD'})
chk('非法变更类型被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/contracts/999999999/changes' % (), {'changeType': 'OTHER'})
chk('合同不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

# ---------- 7. 查询 ----------
st, r = call('GET', '/api/v1/contract-changes?pageNum=1&pageSize=20&contractId=%s' % cid)
chk('变更分页（按合同）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 3,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/contract-changes?pageNum=1&pageSize=20&status=APPROVED')
chk('按状态筛（已批准）', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/contract-changes/999999999')
chk('变更单不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
