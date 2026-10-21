# -*- coding: utf-8 -*-
"""欠费停权处置 · 验证（安全底线为重点）"""
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
print(' 欠费停权处置 · 验证（含安全底线）')
print('=' * 76)

# ---------- 造数据：小区 + 房间 + 房源 + 合同 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'AR-' + sfx, 'orgName': '欠费验证小区',
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
rm = mkspace(fl, '101', 'ROOM', 'R-' + sfx, '90')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'AH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '90'})
house = (r.get('data') or {}).get('id')

st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 4001, 'lesseeName': '欠费张三',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('造生效合同', bool(cid), cid)

# ---------- 造逾期账单（用于扫描）----------
for i, (amt, due) in enumerate([('1000', '2026-02-10'), ('1200', '2026-03-10'),
                                ('800', '2026-04-10')]):
    call('POST', '/api/v1/fin/bills', {
        'feeItemId': 1, 'orgId': int(org), 'contractId': int(cid), 'houseId': int(house),
        'personId': 4001, 'payerName': '欠费张三', 'billPeriod': '2026-0%d' % (i + 1),
        'periodStart': due[:8] + '01', 'periodEnd': due, 'billAmount': amt,
        'dueDate': due, 'generateType': 'MANUAL'})
chk('造 3 张逾期账单', True)

# ---------- 1. 欠费扫描 ----------
st, r = call('GET', '/api/v1/fin/arrears/scan?minOverdueDays=1')
chk('⭐ 欠费扫描接口', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
scan = r.get('data') or []
mine = next((x for x in scan if str(x.get('contractId')) == str(cid)), None)
chk('⭐ 扫到本合同欠费', mine is not None, len(scan))
if mine:
    print('     欠费 %s，逾期 %s 天，%s 张账单，建议冻结=%s'
          % (mine.get('arrearsAmount'), mine.get('overdueDays'), mine.get('billCount'),
             mine.get('freezeRecommended')))
    chk('⭐ 欠费合计 3000.00', str(mine.get('arrearsAmount')) == '3000.00',
        mine.get('arrearsAmount'))
    chk('⭐ 账单张数 3', str(mine.get('billCount')) == '3', mine.get('billCount'))
    chk('⭐ 逾期>30天建议冻结', mine.get('freezeRecommended') in (True, 'true'),
        mine.get('freezeRecommended'))

st, r = call('GET', '/api/v1/fin/arrears/scan?minOverdueDays=99999')
chk('⭐ 阈值过滤（无结果）', len(r.get('data') or []) == 0, len(r.get('data') or []))

# ---------- 2. ⭐ 安全底线：ALL 需显式确认 ----------
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '3000', 'overdueDays': 60,
    'actionType': 'FREEZE', 'freezeScope': 'ALL'})
chk('⭐⭐ 冻结范围 ALL 未确认风险 → 拒绝', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息包含消防/应急安全提示',
    ('消防' in str(r.get('message')) or '安全' in str(r.get('message'))), r.get('message'))
chk('拒绝信息推荐 EXCLUDE_MAIN_DOOR',
    'EXCLUDE_MAIN_DOOR' in str(r.get('message')), r.get('message'))

# ---------- 3. 默认范围 = 排除大门（安全）----------
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '3000', 'overdueDays': 60,
    'actionType': 'FREEZE'})
chk('⭐ 不传冻结范围 → 创建成功', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
a1 = r.get('data') or {}
aid = a1.get('id')
chk('⭐ 默认范围 EXCLUDE_MAIN_DOOR', a1.get('freezeScope') == 'EXCLUDE_MAIN_DOOR',
    a1.get('freezeScope'))
chk('⭐ 范围标签含"安全底线"', '安全底线' in str(a1.get('freezeScopeLabel')),
    a1.get('freezeScopeLabel'))
chk('⭐ freezesMainDoor=false（未停大门）', a1.get('freezesMainDoor') in (False, 'false'),
    a1.get('freezesMainDoor'))
chk('初始状态 PENDING/待执行', a1.get('actionStatus') == 'PENDING'
    and a1.get('actionStatusLabel') == '待执行', a1.get('actionStatus'))
chk('单号 FA 开头', str(a1.get('actionNo', '')).startswith('FA'), a1.get('actionNo'))

# ---------- 4. 显式确认后可 ALL（留审计）----------
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '3000',
    'actionType': 'FREEZE', 'freezeScope': 'ALL', 'confirmSafetyRisk': True})
chk('⭐ 显式确认风险后 ALL 允许（留审计）', r.get('code') == 'BP00000', r.get('code'))
chk('ALL 标记 freezesMainDoor=true',
    (r.get('data') or {}).get('freezesMainDoor') in (True, 'true'),
    (r.get('data') or {}).get('freezesMainDoor'))

# ---------- 5. 执行 + 状态机 ----------
st, r = call('POST', '/api/v1/fin/arrears/%s/execute' % aid, {})
chk('⭐ 执行成功 → EXECUTED', (r.get('data') or {}).get('actionStatus') == 'EXECUTED',
    str(r.get('code')) + ' ' + str((r.get('data') or {}).get('actionStatus')))
chk('执行时间已记录', bool((r.get('data') or {}).get('executeTime')),
    (r.get('data') or {}).get('executeTime'))
st, r = call('POST', '/api/v1/fin/arrears/%s/execute' % aid, {})
chk('⭐ 重复执行被拒', r.get('code') == 'BP40001', r.get('code'))

# ---------- 6. 缴清撤销 ----------
st, r = call('POST', '/api/v1/fin/arrears/%s/revoke' % aid, {'reason': '已缴清全部欠费'})
chk('⭐ 撤销 → REVOKED', (r.get('data') or {}).get('actionStatus') == 'REVOKED',
    str(r.get('code')) + ' ' + str((r.get('data') or {}).get('actionStatus')))
chk('撤销原因已记录', (r.get('data') or {}).get('revokeReason') == '已缴清全部欠费',
    (r.get('data') or {}).get('revokeReason'))
chk('撤销标签=已撤销', (r.get('data') or {}).get('actionStatusLabel') == '已撤销',
    (r.get('data') or {}).get('actionStatusLabel'))
st, r = call('POST', '/api/v1/fin/arrears/%s/execute' % aid, {})
chk('⭐ REVOKED 终态不可再执行', r.get('code') == 'BP40001', r.get('code'))

# ---------- 7. 通知类处置 ----------
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '1000', 'overdueDays': 10,
    'actionType': 'NOTIFY', 'triggerType': 'AUTO'})
nid = (r.get('data') or {}).get('id')
chk('创建通知类处置', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/fin/arrears/%s/execute' % nid, {})
chk('通知类可执行（无需授权联动）',
    (r.get('data') or {}).get('actionStatus') == 'EXECUTED', r.get('code'))

# ---------- 8. 校验 ----------
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '0', 'actionType': 'FREEZE'})
chk('欠费金额 0 被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '100', 'actionType': 'BAD'})
chk('非法处置动作被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': int(cid), 'personId': 4001, 'arrearsAmount': '100',
    'actionType': 'FREEZE', 'freezeScope': 'BAD'})
chk('非法冻结范围被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/fin/arrears', {
    'contractId': 999999999, 'personId': 4001, 'arrearsAmount': '100',
    'actionType': 'FREEZE'})
chk('合同不存在（执行时校验）', bool((r.get('data') or {}).get('id'))
    or r.get('code') != 'BP00000', r.get('code'))
if (r.get('data') or {}).get('id'):
    st2, r2 = call('POST', '/api/v1/fin/arrears/%s/execute' % r.get('data', {}).get('id'), {})
    chk('⭐ 执行时合同缺失 BP30001', r2.get('code') == 'BP30001', r2.get('code'))

# ---------- 9. 查询 ----------
st, r = call('GET', '/api/v1/fin/arrears?pageNum=1&pageSize=20&contractId=%s' % cid)
chk('按合同查处置单', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 3,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/fin/arrears?pageNum=1&pageSize=20&actionType=FREEZE')
chk('按动作筛', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/fin/arrears/by-contract/%s' % cid)
chk('⭐ 按合同列历史', r.get('code') == 'BP00000' and len(r.get('data') or []) >= 3,
    len(r.get('data') or []))
st, r = call('GET', '/api/v1/fin/arrears/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 76)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 76)
