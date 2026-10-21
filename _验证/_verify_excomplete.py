# -*- coding: utf-8 -*-
"""换房业务落地验证：新合同 + 原合同终止 + 房源状态"""
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
PID = 860000 + int(sfx) % 100000
print('=' * 78)
print(' 换房业务落地 · 新合同/原合同终止/房源状态')
print('=' * 78)

st, r = call('POST', '/api/v1/orgs', {'orgCode': 'XC-' + sfx, 'orgName': '换房落地验证',
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
for rid, code, area in ((rm1, 'XC1-', '50'), (rm2, 'XC2-', '90')):
    st, r = call('POST', '/api/v1/houses', {'spaceId': int(rid), 'houseCode': code + sfx,
                                           'houseName': code + '室',
                                           'houseType': 'PUBLIC_RENTAL', 'area': area})
    houses.append((r.get('data') or {}).get('id'))
oldHouse, newHouse = houses
chk('准备：2 个房源（50㎡ / 90㎡）', all(houses), houses)

st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': PID, 'lesseeName': '落地王五',
    'houseId': int(oldHouse), 'spaceId': int(rm1),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：原合同生效', bool(cid), cid)

# 换房前房源状态
st, r = call('GET', '/api/v1/houses/%s' % oldHouse)
print('     换房前 旧房源状态：%s' % (r.get('data') or {}).get('houseStatus'))
st, r = call('GET', '/api/v1/houses/%s' % newHouse)
print('     换房前 新房源状态：%s' % (r.get('data') or {}).get('houseStatus'))

# ---------- 申请 + 审批 ----------
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(oldHouse),
    'newHouseId': int(newHouse), 'exchangeType': 'VOLUNTARY',
    'exchangeReason': '人口增加需换大户型', 'exchangeReasonCode': 'COHABIT',
    'familySizeBefore': 2, 'familySizeAfter': 5})
exId = (r.get('data') or {}).get('id')
chk('申请换房', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/exchanges/%s/submit' % exId, {})
call('POST', '/api/v1/exchanges/%s/approve' % exId, {'reason': '符合条件'})

# ---------- ⭐ 执行换房 ----------
st, r = call('POST', '/api/v1/exchanges/%s/complete' % exId, {})
chk('⭐ 执行换房完成', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
cmp_ = r.get('data') or {}
newCid = cmp_.get('newContractId')
chk('⭐⭐ 已生成新合同 ID', bool(newCid), newCid)
chk('权限已迁移', cmp_.get('grantMigrated') in (True, 'true'), cmp_.get('grantMigrated'))

# ---------- 原合同已终止 ----------
st, r = call('GET', '/api/v1/contracts/%s' % cid)
old = r.get('data') or {}
chk('⭐⭐ 原合同 → TERMINATED/已终止',
    old.get('contractStatus') == 'TERMINATED', old.get('contractStatus'))
chk('原合同终止原因含换房单号',
    '换房' in str(old.get('terminateReason')), old.get('terminateReason'))
print('     原合同终止原因：%s' % old.get('terminateReason'))

# ---------- 新合同正确 ----------
st, r = call('GET', '/api/v1/contracts/%s' % newCid)
nc = r.get('data') or {}
chk('⭐⭐ 新合同状态 EFFECTIVE/履约中',
    nc.get('contractStatus') == 'EFFECTIVE', nc.get('contractStatus'))
chk('⭐⭐ 新合同指向新房源',
    str(nc.get('houseId')) == str(newHouse), (nc.get('houseId'), newHouse))
chk('⭐⭐ 新合同 parentContractId 指向原合同',
    str(nc.get('parentContractId')) == str(cid),
    (nc.get('parentContractId'), cid))
chk('新合同延续承租人', str(nc.get('lesseePersonId')) == str(PID), nc.get('lesseePersonId'))
chk('新合同延续月租金 1000', str(nc.get('monthlyRent')) == '1000.00', nc.get('monthlyRent'))
chk('⭐ 新合同延续原止租日 2027-12-31',
    nc.get('leaseEnd') == '2027-12-31', nc.get('leaseEnd'))
chk('新合同起租日为换房当日',
    nc.get('leaseStart') == time.strftime('%Y-%m-%d'), nc.get('leaseStart'))
chk('新合同房源地址指向新房源', 'XC2' in str(nc.get('houseAddress')), nc.get('houseAddress'))
chk('⭐ 新合同面积取新房源 90', abs(float(nc.get('houseArea') or 0) - 90.0) < 0.01,
    nc.get('houseArea'))
print('     新合同 %s：房源 %s 租期 %s ~ %s 月租 %s'
      % (nc.get('contractNo'), nc.get('houseId'), nc.get('leaseStart'), nc.get('leaseEnd'),
         nc.get('monthlyRent')))

# ---------- 房源状态 ----------
st, r = call('GET', '/api/v1/houses/%s' % oldHouse)
oh = r.get('data') or {}
chk('⭐⭐ 旧房源 → VACANT/空置待配', oh.get('houseStatus') == 'VACANT',
    oh.get('houseStatus'))
st, r = call('GET', '/api/v1/houses/%s' % newHouse)
nh = r.get('data') or {}
chk('⭐⭐ 新房源 → OCCUPIED/已入住', nh.get('houseStatus') == 'OCCUPIED',
    nh.get('houseStatus'))
print('     换房后 旧房源=%s 新房源=%s' % (oh.get('houseStatus'), nh.get('houseStatus')))

# ---------- 换房后可正常出账（新合同可计费）----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'XC-RENT-' + sfx, 'itemName': '租金', 'itemType': 'RENT',
    'calcMode': 'BY_AREA', 'unitPrice': '12.50', 'unit': '元/㎡·月'})
feeId = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': feeId, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
    'billPeriod': '2026-12', 'orgId': int(org), 'contractIds': [int(newCid)], 'dryRun': True})
d = r.get('data') or {}
gi = (d.get('items') or [{}])[0]
print('     新合同出账试算：%s（面积 %s）' % (gi.get('amount'), gi.get('explain')))
chk('⭐⭐ 新合同可正常出账（按 90㎡）',
    str(gi.get('amount')) == '1125.00', gi.get('amount'))

# ---------- 已完成的换房单计数 ----------
st, r = call('GET', '/api/v1/exchanges/count?oldContractId=%s' % cid)
chk('换房次数统计 = 1', str(r.get('data')) == '1', r.get('data'))
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(newHouse),
    'newHouseId': int(oldHouse), 'exchangeType': 'VOLUNTARY'})
chk('⭐ 原租期已达限换上限', r.get('code') == 'BP40001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
