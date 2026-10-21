# -*- coding: utf-8 -*-
"""换房验证：成都限换 1 次 + 重庆应换不换 1.5 倍"""
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
print(' 换房 · 成都限换1次 + 重庆应换不换1.5倍')
print('=' * 78)

PID = 850000 + int(sfx) % 100000
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'XF-' + sfx, 'orgName': '换房验证小区',
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
rm1 = mkspace(fl, '101', 'ROOM', 'R1-' + sfx, '50')
rm2 = mkspace(fl, '201', 'ROOM', 'R2-' + sfx, '90')

houses = []
for rid, code in ((rm1, 'XF1-'), (rm2, 'XF2-')):
    st, r = call('POST', '/api/v1/houses', {'spaceId': int(rid), 'houseCode': code + sfx,
                                           'houseName': code, 'houseType': 'PUBLIC_RENTAL',
                                           'area': '70'})
    houses.append((r.get('data') or {}).get('id'))
chk('准备：2 个房源', all(houses), houses)

st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': PID, 'lesseeName': '换房李四',
    'houseId': int(houses[0]), 'spaceId': int(rm1),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效（原房源 101）', bool(cid), cid)

# ---------- 1. 申请换房 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'VOLUNTARY',
    'exchangeReason': '家庭人口增加，50㎡ 户型不足', 'exchangeReasonCode': 'BIRTH',
    'familySizeBefore': 2, 'familySizeAfter': 4})
chk('⭐ 申请换房', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
ex = r.get('data') or {}
exId = ex.get('id')
chk('换房单号 EX 开头', str(ex.get('exchangeNo', '')).startswith('EX'), ex.get('exchangeNo'))
chk('类型标签=自愿换房', ex.get('exchangeTypeLabel') == '自愿换房', ex.get('exchangeTypeLabel'))
chk('状态 APPLYING/申请中', ex.get('exchangeStatus') == 'APPLYING', ex.get('exchangeStatus'))
chk('⭐ 本租期第 1 次换房', str(ex.get('exchangeTimes')) == '1', ex.get('exchangeTimes'))
chk('未达限换上限', ex.get('exchangeLimitReached') in (False, 'false'),
    ex.get('exchangeLimitReached'))
chk('权限未迁移', ex.get('grantMigrated') in (False, 'false'), ex.get('grantMigrated'))
chk('家庭人数 2 → 4', str(ex.get('familySizeBefore')) == '2'
    and str(ex.get('familySizeAfter')) == '4',
    (ex.get('familySizeBefore'), ex.get('familySizeAfter')))

# 新房源与原相同
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[0]), 'exchangeType': 'VOLUNTARY'})
chk('⭐ 新房源与原房源相同被拒', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 新房源不存在
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(houses[0]),
    'newHouseId': 999999999, 'exchangeType': 'VOLUNTARY'})
chk('新房源不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

# 非法类型
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'BAD'})
chk('非法换房类型被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 2. 状态机 ----------
st, r = call('POST', '/api/v1/exchanges/%s/complete' % exId, {})
chk('⭐ 申请中不可直接完成（不可跳步）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/exchanges/%s/submit' % exId, {})
chk('提交审批 → APPROVING', (r.get('data') or {}).get('exchangeStatus') == 'APPROVING',
    r.get('code'))
st, r = call('POST', '/api/v1/exchanges/%s/approve' % exId, {'reason': '符合换房条件'})
chk('批准 → APPROVED', (r.get('data') or {}).get('exchangeStatus') == 'APPROVED', r.get('code'))
chk('审批意见已记录', '符合换房条件' in str((r.get('data') or {}).get('exchangeReason')),
    (r.get('data') or {}).get('exchangeReason'))

# ---------- 3. ⭐ 执行换房：权限迁移 ----------
st, r = call('POST', '/api/v1/exchanges/%s/complete' % exId, {})
cmp_ = r.get('data') or {}
chk('⭐ 执行换房 → COMPLETED/已完成', cmp_.get('exchangeStatus') == 'COMPLETED',
    r.get('code'))
chk('⭐⭐ 权限已自动迁移', cmp_.get('grantMigrated') in (True, 'true'),
    cmp_.get('grantMigrated'))
chk('已完成不可再操作', r.get('code') == 'BP00000', r.get('code'))

st, r = call('GET', '/api/v1/exchanges/count?oldContractId=%s' % cid)
chk('⭐ 已完成换房次数 = 1', str(r.get('data')) == '1',
    str(r.get('code')) + ' ' + str(r.get('data')))

# ---------- 4. ⭐⭐ 成都限换 1 次 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(houses[1]),
    'newHouseId': int(houses[0]), 'exchangeType': 'VOLUNTARY',
    'exchangeReason': '想再换一次'})
chk('⭐⭐ 同租期第 2 次换房 → 被拒（成都限 1 次）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息含"限 1 次"', '1 次' in str(r.get('message')), r.get('message'))

# ---------- 5. 处理中的换房单不可重复申请 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid) + 1, 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'VOLUNTARY'})
ex2 = (r.get('data') or {}).get('id')
chk('另一合同可申请（不受限）', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid) + 1, 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'VOLUNTARY'})
chk('⭐ 已有处理中换房单 → 拒绝重复申请', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 6. ⭐⭐ 重庆应换不换 1.5 倍 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid) + 2, 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'ADJUST',
    'exchangeReason': '期满合住人数减少，不符合户型标准', 'forceExchange': True})
forced = (r.get('data') or {}).get('id')
chk('创建「应当换房」单', r.get('code') == 'BP00000', r.get('code'))
chk('⭐ forced=true', (r.get('data') or {}).get('forced') in (True, 'true'),
    (r.get('data') or {}).get('forced'))
chk('初始无租金倍率', (r.get('data') or {}).get('rentMultiplier') is None,
    (r.get('data') or {}).get('rentMultiplier'))

# 非"应换房"的单据不能标记
st, r = call('POST', '/api/v1/exchanges/%s/no-exchange' % ex2,
             {'reason': '住户拒绝换房'})
chk('⭐ 非应换房单据不可标记应换不换', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/exchanges/%s/no-exchange' % forced,
             {'reason': '住户拒绝换房，继续占用大户型'})
ne = r.get('data') or {}
chk('⭐⭐ 标记应换不换', ne.get('noExchangeFlag') in (True, 'true'),
    ne.get('noExchangeFlag'))
chk('⭐⭐ 租金倍率 = 1.5（重庆政策）',
    abs(float(ne.get('rentMultiplier') or 0) - 1.5) < 1e-6, ne.get('rentMultiplier'))
chk('原因已记录', '应换不换' in str(ne.get('exchangeReason')), ne.get('exchangeReason'))

# ---------- 7. 驳回 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid) + 3, 'oldHouseId': int(houses[0]),
    'newHouseId': int(houses[1]), 'exchangeType': 'VOLUNTARY'})
ex3 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/exchanges/%s/submit' % ex3, {})
st, r = call('POST', '/api/v1/exchanges/%s/reject' % ex3, {'reason': '无正当理由'})
chk('驳回 → REJECTED', (r.get('data') or {}).get('exchangeStatus') == 'REJECTED',
    r.get('code'))
chk('驳回原因已记录', '无正当理由' in str((r.get('data') or {}).get('exchangeReason')),
    (r.get('data') or {}).get('exchangeReason'))
st, r = call('POST', '/api/v1/exchanges/%s/approve' % ex3, {})
chk('⭐ REJECTED 终态不可再批准', r.get('code') == 'BP40001', r.get('code'))

# ---------- 8. 查询 ----------
st, r = call('GET', '/api/v1/exchanges?pageNum=1&pageSize=20&personId=%s' % PID)
chk('换房分页（按人）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 3,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/exchanges?pageNum=1&pageSize=20&oldContractId=%s' % cid)
chk('按原合同筛', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/exchanges/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
