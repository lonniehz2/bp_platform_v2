# -*- coding: utf-8 -*-
"""同住人 + 补贴按人计费联动验证"""
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
print(' 同住人 + 补贴按人计费 · 联动验证')
print('=' * 78)

# ---------- 准备 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'CH-' + sfx, 'orgName': '同住人验证小区',
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
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'CHH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 8001, 'lesseeName': '同住人李四',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效', bool(cid), cid)

# ---------- 1. 初始保障人口 = 1（仅承租人）----------
st, r = call('GET', '/api/v1/contracts/%s/cohabitants/household-size' % cid)
chk('⭐ 初始保障人口 = 1（仅承租人）', str(r.get('data')) == '1',
    str(r.get('code')) + ' ' + str(r.get('data')))
st, r = call('GET', '/api/v1/contracts/%s/cohabitants' % cid)
chk('初始无同住人', len(r.get('data') or []) == 0, r.get('data'))

# ---------- 2. 添加同住人 ----------
members = [
    ('张美丽', 'SPOUSE', '110101********1234'),
    ('李小宝', 'CHILD', '110101********5678'),
    ('李父', 'PARENT', None),
]
ids = []
for nm, rel, mask in members:
    b = {'memberName': nm, 'relation': rel}
    if mask:
        b['idCardMask'] = mask
    st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % cid, b)
    chk('添加同住人 %s（%s）' % (nm, rel), r.get('code') == 'BP00000',
        str(r.get('code')) + ' ' + str(r.get('message')))
    d = r.get('data') or {}
    ids.append(d.get('id'))
    if nm == '张美丽':
        chk('关系标签=配偶', d.get('relationLabel') == '配偶', d.get('relationLabel'))
        chk('⭐ 身份证仅存脱敏串', d.get('idCardMask') == '110101********1234',
            d.get('idCardMask'))
        chk('初始未授权开门', d.get('granted') in (False, 'false'), d.get('granted'))

st, r = call('GET', '/api/v1/contracts/%s/cohabitants' % cid)
chk('同住人列表 3 人', len(r.get('data') or []) == 3, len(r.get('data') or []))

# ---------- 3. ⭐ 保障人口 = 4（1+3）----------
st, r = call('GET', '/api/v1/contracts/%s/cohabitants/household-size' % cid)
chk('⭐⭐ 保障人口 = 1 + 3 = 4', str(r.get('data')) == '4',
    str(r.get('code')) + ' ' + str(r.get('data')))

# ---------- 4. ⭐ 补贴按人计费自动用真实人口 ----------
st, r = call('POST', '/api/v1/fin/subsidies/standards', {
    'standardCode': 'CH-PERSON-' + sfx, 'standardName': '按人补贴', 'securityType': 'PUBLIC',
    'subsidyMode': 'BY_PERSON', 'subsidyValue': '300', 'effectiveStart': '2026-01-01'})
stdId = (r.get('data') or {}).get('id')
chk('建按人补贴标准（300/人）', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/fin/subsidies/calc', {
    'contractId': int(cid), 'standardId': stdId})
d = r.get('data') or {}
print('     试算：%s' % d.get('explain'))
print('     金额：%s' % d.get('cappedAmount'))
chk('⭐⭐ 补贴按 4 人计 = 300 × 4 = 1200.00',
    str(d.get('cappedAmount')) == '1200.00', d.get('cappedAmount'))
chk('计算说明含"4 人"', '4 人' in str(d.get('explain')), d.get('explain'))

# ---------- 5. 移除同住人后人口下降 ----------
st, r = call('DELETE', '/api/v1/contracts/%s/cohabitants/%s' % (cid, ids[2]))
chk('移除同住人', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
st, r = call('GET', '/api/v1/contracts/%s/cohabitants/household-size' % cid)
chk('⭐ 移除后保障人口 = 3', str(r.get('data')) == '3', r.get('data'))
st, r = call('POST', '/api/v1/fin/subsidies/calc', {
    'contractId': int(cid), 'standardId': stdId})
chk('⭐ 补贴随人口变为 900.00',
    str((r.get('data') or {}).get('cappedAmount')) == '900.00',
    (r.get('data') or {}).get('cappedAmount'))

# ---------- 6. 门禁授权 ----------
st, r = call('POST', '/api/v1/contracts/%s/cohabitants/%s/grant' % (cid, ids[0]),
             {'granted': True})
chk('⭐ 同住人开门授权', (r.get('data') or {}).get('granted') in (True, 'true'),
    r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/cohabitants/%s/grant' % (cid, ids[0]),
             {'granted': False})
chk('撤销开门授权', (r.get('data') or {}).get('granted') in (False, 'false'), r.get('code'))

# ---------- 7. 校验 ----------
st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % cid, {'memberName': '张美丽'})
chk('⭐ 同合同同名重复被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % cid, {'memberName': ''})
chk('空姓名被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/contracts/999999999/cohabitants', {'memberName': '张三'})
chk('合同不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))
st, r = call('GET', '/api/v1/contracts/%s/cohabitants/999999999' % cid)
chk('同住人不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))
st, r = call('DELETE', '/api/v1/contracts/%s/cohabitants/999999999' % cid)
chk('删除不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

# 未知关系归一为 OTHER
st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % cid,
             {'memberName': '远房亲戚', 'relation': 'WEIRD'})
chk('未知关系归一为"其他"', (r.get('data') or {}).get('relation') == 'OTHER'
    and (r.get('data') or {}).get('relationLabel') == '其他',
    (r.get('data') or {}).get('relation'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
