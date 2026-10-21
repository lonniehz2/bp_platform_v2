# -*- coding: utf-8 -*-
"""批量出账验证：先造真实空间+房源+合同，再验证"""
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
        with urllib.request.urlopen(r, timeout=30) as x:
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
print(' 批量自动出账 · 真实数据全链路验证')
print('=' * 74)

# ---------- 1. 造空间树 + 房源 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'BG-' + sfx, 'orgName': '出账验证小区',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')
chk('建小区', r.get('code') == 'BP00000', r.get('code'))


def mk(parent, name, typ, code, area=None):
    b = {'orgId': int(org), 'spaceCode': code, 'spaceName': name, 'spaceType': typ}
    if parent:
        b['parentId'] = int(parent)
    if area:
        b['area'] = area
    st, rr = call('POST', '/api/v1/spaces', b)
    return (rr.get('data') or {}).get('id')


bid = mk(None, '1幢', 'BUILDING', 'B-' + sfx)
uid = mk(bid, '1单元', 'UNIT', 'U-' + sfx)
fid = mk(uid, '1层', 'FLOOR', 'F-' + sfx)
rid = mk(fid, '101室', 'ROOM', 'R-' + sfx, '89.50')
chk('空间树 + 房间（含面积 89.50）', all([bid, uid, fid, rid]), (bid, uid, fid, rid))

st, r = call('POST', '/api/v1/houses', {
    'spaceId': int(rid), 'houseCode': 'H-' + sfx, 'houseName': '101室房源',
    'houseType': 'PUBLIC_RENTAL', 'area': '89.50'})
house = (r.get('data') or {}).get('id')
chk('建房源（面积 89.50）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
chk('房源面积已存 89.5', str((r.get('data') or {}).get('area')) == '89.5',
    (r.get('data') or {}).get('area'))

# ---------- 2. 造生效合同 ----------
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4001, 'lesseeName': '出账张三',
    'houseId': int(house), 'spaceId': int(rid), 'houseAddress': '1幢101室',
    'houseArea': '89.50', 'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
st, r = call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('合同生效', (r.get('data') or {}).get('contractStatus') == 'EFFECTIVE', r.get('code'))

# ---------- 3. 收费项目 ----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BA-RENT-' + sfx, 'itemName': '保障房租金', 'itemType': 'RENT',
    'calcMode': 'BY_AREA', 'unitPrice': '12.50', 'unit': '元/㎡·月'})
itemId = (r.get('data') or {}).get('id')
chk('收费项目（按面积 12.50）', r.get('code') == 'BP00000', r.get('code'))

# ---------- 4. 试运行 ----------
period = '2026-11'
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'dueDate': '2026-11-10', 'orgId': int(org),
    'contractIds': [int(cid)], 'dryRun': True})
chk('⭐ 试运行', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
d = r.get('data') or {}
mine = (d.get('items') or [{}])[0]
print('     试算：数量=%s 金额=%s 说明=%s' % (mine.get('quantity'), mine.get('amount'),
                                           mine.get('explain')))
chk('⭐ 试运行 dryRun=true', d.get('dryRun') in (True, 'true'), d.get('dryRun'))
chk('⭐ 试运行算费成功', d.get('generated') == 1, d.get('generated'))
chk('⭐ 金额 = 89.50 × 12.50 = 1118.75', str(mine.get('amount')) == '1118.75',
    mine.get('amount'))
chk('⭐ 试运行不落库', mine.get('billId') is None, mine.get('billId'))

# ---------- 5. 落库 ----------
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'dueDate': '2026-11-10', 'orgId': int(org),
    'contractIds': [int(cid)], 'dryRun': False})
g = r.get('data') or {}
gi = (g.get('items') or [{}])[0]
chk('⭐ 落库生成 1 张', g.get('generated') == 1, g.get('generated'))
chk('⭐ 生成的账单有 ID', gi.get('billId') is not None, gi.get('billId'))
chk('合计金额 1118.75', str(g.get('totalAmount')) == '1118.75', g.get('totalAmount'))
billId = gi.get('billId')

# ---------- 6. 幂等 ----------
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'orgId': int(org), 'contractIds': [int(cid)], 'dryRun': False})
g2 = r.get('data') or {}
g2i = (g2.get('items') or [{}])[0]
chk('⭐ 幂等：生成 0 张', g2.get('generated') == 0, g2.get('generated'))
chk('⭐ 幂等：跳过且说明"已存在"', '已存在' in str(g2i.get('reason')), g2i.get('reason'))

# ---------- 7. 账单可查且字段正确 ----------
st, r = call('GET', '/api/v1/fin/bills/%s' % billId)
b1 = r.get('data') or {}
chk('账单状态 UNPAID', b1.get('billStatus') == 'UNPAID', b1.get('billStatus'))
chk('⭐ generateType=AUTO', b1.get('generateType') == 'AUTO', b1.get('generateType'))
chk('账期 2026-11', b1.get('billPeriod') == period, b1.get('billPeriod'))
chk('应收 = 应付 = 1118.75', str(b1.get('billAmount')) == '1118.75'
    and str(b1.get('payableAmount')) == '1118.75',
    (b1.get('billAmount'), b1.get('payableAmount')))
chk('关联合同/房源已回填',
    str(b1.get('contractId')) == str(cid) and str(b1.get('houseId')) == str(house),
    (b1.get('contractId'), b1.get('houseId')))

# ---------- 8. 出账后可收款核销 ----------
st, r = call('POST', '/api/v1/fin/payments', {
    'orgId': int(org), 'personId': 4001, 'payerName': '出账张三',
    'payAmount': '1118.75', 'payChannel': 'WECHAT'})
pid = (r.get('data') or {}).get('id')
chk('对自动账单登记收款', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/fin/payments/%s/allocate' % pid,
             {'billId': billId, 'amount': '1118.75'})
chk('⭐ 自动账单可核销至 PAID', (r.get('data') or {}).get('billStatus') == 'PAID',
    (r.get('data') or {}).get('billStatus'))

# ---------- 9. 缺面积时给明确原因 ----------
st, r = call('POST', '/api/v1/houses', {
    'spaceId': int(rid), 'houseCode': 'H2-' + sfx, 'houseName': '无面积房源',
    'houseType': 'PUBLIC_RENTAL'})
house2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4002, 'lesseeName': '无面积李四',
    'houseId': int(house2), 'spaceId': int(rid),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '0', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid2, {})
call('POST', '/api/v1/contracts/%s/sign' % cid2, {})
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
    'billPeriod': '2026-12', 'orgId': int(org), 'contractIds': [int(cid2)], 'dryRun': True})
gi2 = ((r.get('data') or {}).get('items') or [{}])[0]
print('     缺面积原因：%s' % gi2.get('reason'))
chk('⭐ 缺面积给明确原因（不再误报"金额为0"）',
    '未录入建筑面积' in str(gi2.get('reason')), gi2.get('reason'))

# ---------- 10. 按夜批量（民宿业态）----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BA-NIGHT-' + sfx, 'itemName': '民宿房费', 'itemType': 'RENT',
    'calcMode': 'BY_NIGHT', 'unitPrice': '300', 'unit': '元/套·夜'})
nightItem = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': nightItem, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-06',
    'billPeriod': '2026-11-N', 'orgId': int(org), 'contractIds': [int(cid)], 'dryRun': True})
ni = ((r.get('data') or {}).get('items') or [{}])[0]
print('     按夜：数量=%s 金额=%s' % (ni.get('quantity'), ni.get('amount')))
chk('⭐ 按夜数量 = 5 天', str(ni.get('quantity')) == '5', ni.get('quantity'))
chk('⭐ 按夜金额 = 5×300 = 1500.00', str(ni.get('amount')) == '1500.00', ni.get('amount'))

print()
print('-' * 74)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 74)
