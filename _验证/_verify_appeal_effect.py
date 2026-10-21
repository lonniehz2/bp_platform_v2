# -*- coding: utf-8 -*-
"""复议回写原业务验证：异议成立 → 调租真被撤销"""
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
PID = 880000 + int(sfx) % 100000
print('=' * 78)
print(' 复议回写原业务 · 异议成立能否真撤销调租')
print('=' * 78)

# ---------- 准备：合同（月租 1000）----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'AP-' + sfx, 'orgName': '复议回写验证',
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
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'APH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': PID, 'lesseeName': '复议赵六',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效（月租 1000）', bool(cid), cid)

# ---------- 年审 ADJUST：调租 1000 → 1600 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL'})
rid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid, {})
call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {
    'reviewResult': 'ADJUST', 'checkResult': json.dumps({'income': 9000}),
    'adjustContent': '收入超标，租金上浮至 1600'})
st, r = call('POST', '/api/v1/annual-reviews/%s/rent-change' % rid,
             {'newMonthlyRent': '1600', 'reason': '年审调租'})
chgId = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contract-changes/%s/approve' % chgId, {})
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('⭐ 年审调租已生效：租金 1600.00',
    str((r.get('data') or {}).get('monthlyRent')) == '1600.00',
    (r.get('data') or {}).get('monthlyRent'))

# ---------- 住户申诉 ----------
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'ANNUAL_REVIEW', 'bizId': int(rid), 'personId': PID, 'orgId': int(org),
    'appealType': 'SUBMIT',
    'appealReason': '配偶失业未计入，家庭收入实际 5200 元未超标', 'daysFromNow': 10})
apId = (r.get('data') or {}).get('id')
chk('提出申诉', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/appeals/%s/accept' % apId, {'userId': 9001})
call('POST', '/api/v1/appeals/%s/investigate' % apId, {'userId': 9005})

# ---------- ⭐⭐ 判异议成立 → 应真撤销调租 ----------
st, r = call('POST', '/api/v1/appeals/%s/decide' % apId, {
    'decision': 'UPHELD', 'resultEffect': 'RESTORE',
    'handleResult': '核实配偶失业，家庭收入 5200 元未超标',
    'reviewOpinion': '异议成立，恢复原租金标准', 'handleUserId': 9003})
chk('⭐⭐ 判异议成立', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
dec = r.get('data') or {}
print('     复核意见：%s' % dec.get('reviewOpinion'))
chk('⭐ 复核意见记录了处置结果',
    '恢复' in str(dec.get('reviewOpinion')), dec.get('reviewOpinion'))

# 合同租金应真的回到 1000
st, r = call('GET', '/api/v1/contracts/%s' % cid)
now_rent = str((r.get('data') or {}).get('monthlyRent'))
print('     复议后合同租金：%s' % now_rent)
chk('⭐⭐ 合同租金已恢复为 1000.00', now_rent == '1000.00', now_rent)

# 年审结论应改回 KEEP
st, r = call('GET', '/api/v1/annual-reviews/%s' % rid)
rv = r.get('data') or {}
chk('⭐⭐ 年审结论已恢复为 KEEP/保留资格',
    rv.get('reviewResult') == 'KEEP' and rv.get('reviewResultLabel') == '保留资格',
    rv.get('reviewResult'))
chk('⭐ 年审调整内容记录了复议',
    '复议' in str(rv.get('adjustContent')), rv.get('adjustContent'))

# 反向变更单存在且已批准
st, r = call('GET', '/api/v1/contract-changes?pageNum=1&pageSize=20&contractId=%s' % cid)
rows = (r.get('data') or {}).get('rows') or []
reverts = [x for x in rows if '复议恢复' in str(x.get('changeReason'))]
chk('⭐⭐ 已生成反向调租变更单', len(reverts) >= 1, len(reverts))
if reverts:
    chk('反向变更已批准', reverts[0].get('approveStatus') == 'APPROVED',
        reverts[0].get('approveStatus'))
    print('     反向变更：%s → %s（%s）'
          % (reverts[0].get('beforeJson', '')[:40], reverts[0].get('afterJson', '')[:40],
             reverts[0].get('approveStatus')))

# ---------- 退出类复议：撤销腾退单 ----------
PID2 = PID + 1
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': PID2, 'lesseeName': '复议钱七',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid2, {})
call('POST', '/api/v1/contracts/%s/sign' % cid2, {})

st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID2, 'contractId': int(cid2), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL'})
rid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid2, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid2, {
    'reviewResult': 'EXIT', 'adjustContent': '收入严重超标应退出'})
chk('年审 EXIT → 自动生成腾退单', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid2)
trows = (r.get('data') or {}).get('rows') or []
chk('腾退单已生成', len(trows) >= 1, len(trows))
tno = trows[0].get('terminationNo') if trows else None

# 对 EXIT 申诉
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'EXIT', 'bizId': int(rid2), 'personId': PID2, 'orgId': int(org),
    'appealType': 'SUBMIT', 'appealReason': '收入核算有误，不应退出'})
ap2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/appeals/%s/accept' % ap2, {'userId': 9001})
call('POST', '/api/v1/appeals/%s/investigate' % ap2, {'userId': 9005})
st, r = call('POST', '/api/v1/appeals/%s/decide' % ap2, {
    'decision': 'UPHELD', 'resultEffect': 'RESTORE',
    'handleResult': '收入核算确有错误', 'reviewOpinion': '异议成立，撤销腾退决定',
    'handleUserId': 9003})
chk('⭐⭐ 退出类复议判异议成立', r.get('code') == 'BP00000', r.get('code'))
print('     复核意见：%s' % (r.get('data') or {}).get('reviewOpinion'))

st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid2)
trows2 = (r.get('data') or {}).get('rows') or []
cancelled = [x for x in trows2 if x.get('terminationStatus') == 'CANCELLED']
chk('⭐⭐ 腾退单已被撤销', len(cancelled) >= 1,
    [(x.get('terminationNo'), x.get('terminationStatus')) for x in trows2])
if cancelled:
    chk('撤销原因含复议单号',
        '复议' in str(cancelled[0].get('exitReason')), cancelled[0].get('exitReason'))
    print('     腾退单 %s → %s（%s）' % (cancelled[0].get('terminationNo'),
                                      cancelled[0].get('terminationStatus'),
                                      cancelled[0].get('exitReason')))

# ---------- NONE 不影响原业务 ----------
PID3 = PID + 2
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'REVIEW', 'bizId': 12345, 'personId': PID3,
    'appealType': 'SUBMIT', 'appealReason': '审核不合理'})
ap3 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/appeals/%s/accept' % ap3, {'userId': 9001})
call('POST', '/api/v1/appeals/%s/investigate' % ap3, {'userId': 9005})
st, r = call('POST', '/api/v1/appeals/%s/decide' % ap3, {
    'decision': 'REJECTED', 'resultEffect': 'NONE', 'reviewOpinion': '异议不成立'})
chk('⭐ NONE 不改原业务（复核意见无处置记录）',
    '处置' not in str((r.get('data') or {}).get('reviewOpinion')),
    (r.get('data') or {}).get('reviewOpinion'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
