# -*- coding: utf-8 -*-
"""多项目批量出账 · 验证"""
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
print('=' * 74)
print(' 多项目批量出账 · 验证')
print('=' * 74)

# ---------- 准备：小区 + 房间 + 房源 + 合同 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'BT-' + sfx, 'orgName': '批量出账小区',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')


def mkspace(parent, name, typ, code, area=None):
    b = {'orgId': int(org), 'spaceCode': code, 'spaceName': name, 'spaceType': typ}
    if parent:
        b['parentId'] = int(parent)
    if area:
        b['area'] = area
    st, rr = call('POST', '/api/v1/spaces', b)
    return (rr.get('data') or {}).get('id')


b1 = mkspace(None, '1幢', 'BUILDING', 'B1-' + sfx)
u1 = mkspace(b1, '1单元', 'UNIT', 'U1-' + sfx)
f1 = mkspace(u1, '1层', 'FLOOR', 'F1-' + sfx)
r1 = mkspace(f1, '101室', 'ROOM', 'R1-' + sfx, '100')
r2 = mkspace(f1, '102室', 'ROOM', 'R2-' + sfx, '80')
chk('建空间树（两个房间 100㎡ / 80㎡）', all([b1, u1, f1, r1, r2]), (r1, r2))

st, r = call('POST', '/api/v1/houses', {'spaceId': int(r1), 'houseCode': 'BH1-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '100'})
h1 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(r2), 'houseCode': 'BH2-' + sfx,
                                       'houseName': '102', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
h2 = (r.get('data') or {}).get('id')
chk('建两个房源', bool(h1) and bool(h2), (h1, h2))

cids = []
for h, rid, nm in ((h1, r1, '批量A'), (h2, r2, '批量B')):
    st, r = call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
        'lesseePersonId': 4001, 'lesseeName': nm,
        'houseId': int(h), 'spaceId': int(rid),
        'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
        'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
        'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
        'signType': 'PAPER'})
    c = (r.get('data') or {}).get('id')
    call('POST', '/api/v1/contracts/%s/submit-sign' % c, {})
    call('POST', '/api/v1/contracts/%s/sign' % c, {})
    cids.append(c)
chk('建 2 份生效合同', len([c for c in cids if c]) == 2, cids)

# ---------- 三个收费项目：租金(按面积) / 物业费(按面积) / 车位费(固定) ----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BTR-' + sfx, 'itemName': '保障房租金', 'itemType': 'RENT',
    'calcMode': 'BY_AREA', 'unitPrice': '12.50', 'unit': '元/㎡·月'})
iRent = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BTP-' + sfx, 'itemName': '物业费', 'itemType': 'PROPERTY',
    'calcMode': 'BY_AREA', 'unitPrice': '2.00', 'unit': '元/㎡·月'})
iProp = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BTS-' + sfx, 'itemName': '车位费', 'itemType': 'PARKING',
    'calcMode': 'FIXED', 'unitPrice': '300', 'unit': '元/月'})
iPark = (r.get('data') or {}).get('id')
chk('建 3 个收费项目', all([iRent, iProp, iPark]), (iRent, iProp, iPark))

# ---------- 1. 多项目试运行 ----------
st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [{'feeItemId': iRent}, {'feeItemId': iProp}, {'feeItemId': iPark}],
    'periodStart': '2027-01-01', 'periodEnd': '2027-01-31',
    'billPeriod': '2027-01', 'orgId': int(org), 'contractIds': cids, 'dryRun': True})
chk('⭐ 多项目批量出账接口', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
d = r.get('data') or {}
chk('返回批次号', str(d.get('batchNo', '')).startswith('GB'), d.get('batchNo'))
chk('dryRun=true', d.get('dryRun') in (True, 'true'), d.get('dryRun'))
chk('⭐ 3 个项目全部 OK',
    all(x.get('status') == 'OK' for x in (d.get('results') or [])),
    [(x.get('feeItemName'), x.get('status')) for x in (d.get('results') or [])])
print('     生成 %s 张，跳过 %s，合计 %s'
      % (d.get('totalGenerated'), d.get('totalSkipped'), d.get('totalAmount')))
# 租金：(100+80)×12.5 = 2250；物业：(100+80)×2 = 360；车位：300×2 = 600 → 3210
chk('⭐ 合计 = 2250 + 360 + 600 = 3210.00', str(d.get('totalAmount')) == '3210.00',
    d.get('totalAmount'))
chk('⭐ 应生成 6 张（3 项目 × 2 合同）', str(d.get('totalGenerated')) == '6',
    d.get('totalGenerated'))

byName = {x.get('feeItemName'): x for x in (d.get('results') or [])}
chk('⭐ 租金项目合计 2250.00',
    str((byName.get('保障房租金') or {}).get('detail', {}).get('totalAmount')) == '2250.00',
    (byName.get('保障房租金') or {}).get('detail', {}).get('totalAmount'))
chk('⭐ 物业费合计 360.00',
    str((byName.get('物业费') or {}).get('detail', {}).get('totalAmount')) == '360.00',
    (byName.get('物业费') or {}).get('detail', {}).get('totalAmount'))
chk('⭐ 车位费合计 600.00',
    str((byName.get('车位费') or {}).get('detail', {}).get('totalAmount')) == '600.00',
    (byName.get('车位费') or {}).get('detail', {}).get('totalAmount'))

# ---------- 2. 落库 ----------
st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [{'feeItemId': iRent}, {'feeItemId': iProp}, {'feeItemId': iPark}],
    'periodStart': '2027-01-01', 'periodEnd': '2027-01-31',
    'billPeriod': '2027-01', 'orgId': int(org), 'contractIds': cids, 'dryRun': False})
g = r.get('data') or {}
chk('⭐ 落库生成 6 张', str(g.get('totalGenerated')) == '6', g.get('totalGenerated'))
chk('落库合计 3210.00', str(g.get('totalAmount')) == '3210.00', g.get('totalAmount'))

# ---------- 3. 幂等 ----------
st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [{'feeItemId': iRent}, {'feeItemId': iProp}],
    'periodStart': '2027-01-01', 'periodEnd': '2027-01-31',
    'billPeriod': '2027-01', 'orgId': int(org), 'contractIds': cids, 'dryRun': False})
g2 = r.get('data') or {}
chk('⭐ 幂等：重复执行生成 0 张', str(g2.get('totalGenerated')) == '0', g2.get('totalGenerated'))
chk('⭐ 幂等：全部跳过 4 张', str(g2.get('totalSkipped')) == '4', g2.get('totalSkipped'))

# ---------- 4. 项目间隔离：坏项目不影响好项目 ----------
st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [{'feeItemId': iRent}, {'feeItemId': 999999999}],
    'periodStart': '2027-02-01', 'periodEnd': '2027-02-28',
    'billPeriod': '2027-02', 'orgId': int(org), 'contractIds': cids, 'dryRun': True})
iso = r.get('data') or {}
rs = {x.get('feeItemId'): x for x in (iso.get('results') or [])}
chk('⭐ 坏项目返回 FAILED（不抛异常）',
    (rs.get(999999999) or {}).get('status') == 'FAILED',
    (rs.get(999999999) or {}).get('status'))
chk('⭐ 好项目仍正常 OK（项目间隔离）',
    (rs.get(iRent) or {}).get('status') == 'OK',
    (rs.get(iRent) or {}).get('status'))
chk('好项目仍产生金额', str((rs.get(iRent) or {}).get('detail', {}).get('totalAmount'))
    == '2250.00', (rs.get(iRent) or {}).get('detail', {}).get('totalAmount'))

# ---------- 5. 校验 ----------
st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [], 'periodStart': '2027-01-01', 'periodEnd': '2027-01-31'})
chk('空项目列表被拒', r.get('code') == 'BP10001', r.get('code'))

st, r = call('POST', '/api/v1/fin/bills/generate-batch', {
    'items': [{'feeItemId': iRent}],
    'periodStart': '2027-01-31', 'periodEnd': '2027-01-01'})
chk('截止日早于起始日被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 6. 出账后可查可收 ----------
st, r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=50&contractId=%s' % cids[0])
rows = (r.get('data') or {}).get('rows') or []
autoBills = [x for x in rows if x.get('generateType') == 'AUTO']
chk('⭐ 该合同有 3 张 AUTO 账单（租金+物业+车位）', len(autoBills) >= 3, len(autoBills))
names = sorted([x.get('billPeriod') for x in autoBills])
chk('账期均为 2027-01', all(n == '2027-01' for n in names), names)
total = sum(float(x.get('billAmount') or 0) for x in autoBills
            if x.get('billPeriod') == '2027-01')
# 100㎡: 租金1250 + 物业200 + 车位300 = 1750
chk('⭐ 单户合计 1250+200+300 = 1750', abs(total - 1750.0) < 0.01, total)

print()
print('-' * 74)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 74)
