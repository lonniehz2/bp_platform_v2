# -*- coding: utf-8 -*-
"""补贴标准与发放 · 验证（四种补贴方式 + 抵扣租金）"""
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
print(' 补贴标准与发放 · 验证（广州双轨）')
print('=' * 76)

# ---------- 造数据 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'SB-' + sfx, 'orgName': '补贴验证小区',
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


bd = mkspace(None, '1幢', 'BUILDING', 'B-' + sfx)
un = mkspace(bd, '1单元', 'UNIT', 'U-' + sfx)
fl = mkspace(un, '1层', 'FLOOR', 'F-' + sfx)
rm = mkspace(fl, '101', 'ROOM', 'R-' + sfx, '80')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'SH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')

st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4001, 'lesseeName': '补贴张三',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('造合同（80㎡ 月租 1000）', bool(cid), cid)

# ---------- 1. 四种补贴标准 ----------
standards = {}
for code, name, mode, value, cap, stype in [
        ('SUB-FIXED', '低保户定额补贴', 'FIXED', '800', None, 'PUBLIC'),
        ('SUB-AREA', '按面积补贴', 'BY_AREA', '20', '1500', 'PUBLIC'),
        ('SUB-PERSON', '按人补贴', 'BY_PERSON', '300', None, 'PUBLIC'),
        ('SUB-RATIO', '按租金比例补贴', 'RATIO', '0.6', None, 'PUBLIC')]:
    b = {'standardCode': code + '-' + sfx, 'standardName': name, 'securityType': stype,
         'subsidyMode': mode, 'subsidyValue': value,
         'effectiveStart': '2026-01-01'}
    if cap:
        b['maxAmount'] = cap
    st, r = call('POST', '/api/v1/fin/subsidies/standards', b)
    standards[mode] = (r.get('data') or {}).get('id')
    chk('建标准·%s（%s）' % (mode, name), r.get('code') == 'BP00000',
        str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/subsidies/standards', {
    'standardCode': 'SUB-FIXED-' + sfx, 'standardName': '重复', 'securityType': 'PUBLIC',
    'subsidyMode': 'FIXED', 'subsidyValue': '1'})
chk('⭐ 标准编码重复被拒 BP30002', r.get('code') == 'BP30002', r.get('code'))

st, r = call('POST', '/api/v1/fin/subsidies/standards', {
    'standardCode': 'BAD-' + sfx, 'standardName': 'bad', 'securityType': 'PUBLIC',
    'subsidyMode': 'RATIO', 'subsidyValue': '1.5'})
chk('⭐ 比例超过 1（100%）被拒', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 2. 四种方式试算 ----------
st, r = call('POST', '/api/v1/fin/subsidies/calc',
             {'contractId': int(cid), 'standardId': standards['FIXED']})
d = r.get('data') or {}
chk('⭐ 定额：800.00', str(d.get('cappedAmount')) == '800.00', d.get('cappedAmount'))

st, r = call('POST', '/api/v1/fin/subsidies/calc',
             {'contractId': int(cid), 'standardId': standards['BY_AREA']})
d = r.get('data') or {}
chk('⭐ 按面积：20 × 80㎡ = 1600 → 封顶 1500.00',
    str(d.get('cappedAmount')) == '1500.00', d.get('cappedAmount'))
chk('⭐ 封顶前 1600.00', str(d.get('amount')) == '1600.00', d.get('amount'))
chk('⭐ capped=true', d.get('capped') in (True, 'true'), d.get('capped'))
print('     说明：%s' % d.get('explain'))

st, r = call('POST', '/api/v1/fin/subsidies/calc',
             {'contractId': int(cid), 'standardId': standards['BY_PERSON'], 'personCount': 3})
d = r.get('data') or {}
chk('⭐ 按人：300 × 3 人 = 900.00', str(d.get('cappedAmount')) == '900.00',
    d.get('cappedAmount'))

st, r = call('POST', '/api/v1/fin/subsidies/calc',
             {'contractId': int(cid), 'standardId': standards['RATIO']})
d = r.get('data') or {}
chk('⭐ 按租金比例：1000 × 0.6 = 600.00', str(d.get('cappedAmount')) == '600.00',
    d.get('cappedAmount'))

# ---------- 3. 发放 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-06',
    'standardId': standards['FIXED'], 'payMode': 'FINANCE'})
chk('⭐ 发放补贴', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
rec = r.get('data') or {}
rid = rec.get('id')
chk('状态 PENDING/待发放', rec.get('recordStatus') == 'PENDING'
    and rec.get('recordStatusLabel') == '待发放', rec.get('recordStatus'))
chk('单号 FS 开头', str(rec.get('recordNo', '')).startswith('FS'), rec.get('recordNo'))
chk('⭐ 应发金额 800.00', str(rec.get('subsidyAmount')) == '800.00',
    rec.get('subsidyAmount'))

st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-06',
    'standardId': standards['FIXED']})
chk('⭐ 幂等：同合同同期间重复发放被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026/06'})
chk('期间格式错误被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 4. 自动匹配标准 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-07'})
chk('⭐ 不指定标准 → 自动匹配（按合同类型→保障类型）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
if r.get('code') == 'BP00000':
    autoRec = r.get('data') or {}
    chk('自动匹配到标准', bool(autoRec.get('standardId')), autoRec.get('standardId'))
    print('     自动匹配应发：%s' % autoRec.get('subsidyAmount'))

# ---------- 5. 确认发放 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/confirm' % rid,
             {'financeBatchNo': 'FIN-2026-06'})
chk('⭐ 确认发放 → SUCCESS/已发放',
    (r.get('data') or {}).get('recordStatus') == 'SUCCESS', r.get('code'))
chk('实发 800.00', str((r.get('data') or {}).get('paidAmount')) == '800.00',
    (r.get('data') or {}).get('paidAmount'))
chk('发放日期已记录', bool((r.get('data') or {}).get('issueDate')),
    (r.get('data') or {}).get('issueDate'))
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/confirm' % rid, {})
chk('⭐ 重复确认被拒', r.get('code') == 'BP40001', r.get('code'))

# ---------- 6. ⭐ 抵扣租金（OFFSET_RENT）----------
# 造一张 2026-08 租金账单 1000
st, r = call('POST', '/api/v1/fin/bills', {
    'feeItemId': 1, 'orgId': int(org), 'contractId': int(cid), 'houseId': int(house),
    'personId': 4001, 'payerName': '补贴张三', 'billPeriod': '2026-08',
    'periodStart': '2026-08-01', 'periodEnd': '2026-08-31', 'billAmount': '1000',
    'dueDate': '2026-08-10', 'generateType': 'MANUAL'})
billId = (r.get('data') or {}).get('id')
chk('造 8 月租金账单 1000', bool(billId), billId)

st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-08',
    'standardId': standards['FIXED'], 'payMode': 'OFFSET_RENT'})
orid = (r.get('data') or {}).get('id')
chk('发放抵扣租金类补贴（800）', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/confirm' % orid, {})
chk('确认发放（触发抵扣）', (r.get('data') or {}).get('recordStatus') == 'SUCCESS', r.get('code'))

st, r = call('GET', '/api/v1/fin/bills/%s' % billId)
b = r.get('data') or {}
chk('⭐ 账单已免 800.00', str(b.get('waivedAmount')) == '800.00', b.get('waivedAmount'))
chk('⭐ 剩余应付 200.00', str(b.get('payableAmount')) == '200.00', b.get('payableAmount'))
chk('⭐ 账单转 PARTIAL/部分缴', b.get('billStatus') == 'PARTIAL', b.get('billStatus'))

# ---------- 7. 超额实发校验 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records', {
    'contractId': int(cid), 'personId': 4001, 'subsidyPeriod': '2026-09',
    'standardId': standards['FIXED']})
r2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/confirm' % r2,
             {'paidAmount': '9999'})
chk('⭐ 实发不能超应发', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 8. 失败标记 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records/%s/fail' % r2,
             {'reason': '银行账户异常'})
chk('标记发放失败 → FAILED', (r.get('data') or {}).get('recordStatus') == 'FAILED',
    (r.get('data') or {}).get('recordStatus'))
chk('失败原因已记录', (r.get('data') or {}).get('failReason') == '银行账户异常',
    (r.get('data') or {}).get('failReason'))

# ---------- 9. 批量发放 ----------
st, r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2027-03', 'orgId': int(org), 'payMode': 'FINANCE', 'dryRun': True})
chk('⭐ 批量发放（试运行）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
bt = r.get('data') or {}
print('     合同 %s，发放 %s，跳过 %s，合计 %s'
      % (bt.get('total'), bt.get('granted'), bt.get('skipped'), bt.get('totalAmount')))
chk('扫描到生效合同', int(bt.get('total') or 0) >= 1, bt.get('total'))
chk('试运行有结果', int(bt.get('granted') or 0) >= 1, bt.get('granted'))

st, r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2027-03', 'orgId': int(org), 'payMode': 'FINANCE', 'dryRun': False})
b1 = r.get('data') or {}
chk('⭐ 批量落库', int(b1.get('granted') or 0) >= 1, b1.get('granted'))
st, r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2027-03', 'orgId': int(org), 'dryRun': False})
b2 = r.get('data') or {}
chk('⭐ 批量幂等：重复发 0 张', int(b2.get('granted') or 0) == 0, b2.get('granted'))
chk('幂等跳过并说明原因', int(b2.get('skipped') or 0) >= 1, b2.get('skipped'))

st, r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2027-3'})
chk('批量期间格式错误被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 10. 查询 ----------
st, r = call('GET', '/api/v1/fin/subsidies/standards?pageNum=1&pageSize=20&securityType=PUBLIC')
chk('标准分页（按保障类型）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 4,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=20&contractId=%s' % cid)
chk('记录分页（按合同）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 3,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/subsidies/standards/999999999')
chk('标准不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 76)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 76)
