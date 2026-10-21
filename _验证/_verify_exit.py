# -*- coding: utf-8 -*-
"""年审 EXIT → 自动发起退租腾退单 验证"""
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
print(' 年审 EXIT → 自动发起退租腾退单')
print('=' * 78)

st, r = call('POST', '/api/v1/orgs', {'orgCode': 'EX-' + sfx, 'orgName': '退出验证小区',
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
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'EXH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')


def mkcontract(person_id, name):
    st_, rr = call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
        'lesseePersonId': person_id, 'lesseeName': name,
        'houseId': int(house), 'spaceId': int(rm),
        'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
        'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
        'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
        'signType': 'PAPER'})
    c = (rr.get('data') or {}).get('id')
    call('POST', '/api/v1/contracts/%s/submit-sign' % c, {})
    call('POST', '/api/v1/contracts/%s/sign' % c, {})
    return c


PID1 = 800000 + int(sfx) % 100000
PID2 = PID1 + 1
cid = mkcontract(PID1, '退出张三')
chk('准备：合同生效', bool(cid), cid)

# 退租单初始为空
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid)
chk('⭐ 初始无退租单', int((r.get('data') or {}).get('total', 0)) == 0,
    (r.get('data') or {}).get('total'))

# ---------- 1. 年审 KEEP → 不发起腾退 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID1, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL'})
rid_keep = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid_keep, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid_keep,
             {'reviewResult': 'KEEP'})
chk('年审 KEEP 完成', (r.get('data') or {}).get('reviewResult') == 'KEEP', r.get('code'))
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid)
chk('⭐ KEEP 不发起退租单', int((r.get('data') or {}).get('total', 0)) == 0,
    (r.get('data') or {}).get('total'))

# ---------- 2. ⭐⭐ 年审 EXIT → 自动发起腾退单 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID1, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2027', 'reviewType': 'ANNUAL'})
rid = (r.get('data') or {}).get('id')
chk('创建年审单（2027）', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/annual-reviews/%s/start' % rid, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {
    'reviewResult': 'EXIT',
    'checkResult': json.dumps({'income': 15000, 'limit': 6000}),
    'adjustContent': '收入严重超标，不再符合保障条件，应退出保障'})
chk('⭐⭐ 年审 EXIT 完成', (r.get('data') or {}).get('reviewResult') == 'EXIT', r.get('code'))
fin = r.get('data') or {}
chk('⭐⭐ 年审单已回写退租单号',
    '退租单' in str(fin.get('adjustContent')), fin.get('adjustContent'))
print('     调整内容：%s' % fin.get('adjustContent'))

# 检查退租单真的生成了
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid)
total = int((r.get('data') or {}).get('total', 0))
chk('⭐⭐ 已自动生成退租单', total >= 1, total)
rows = (r.get('data') or {}).get('rows') or []
if rows:
    t = rows[0]
    print('     退租单 %s 类型 %s 状态 %s 计划退房 %s'
          % (t.get('terminationNo'), t.get('terminationType'), t.get('terminationStatus'),
             t.get('planExitDate')))
    chk('退租类型 = OTHER（政策性退出，非违规）',
        t.get('terminationType') == 'OTHER', t.get('terminationType'))
    chk('⭐ 未误触发 5 年禁申（banReapplyEndDate 为空）',
        not t.get('banReapplyEndDate'), t.get('banReapplyEndDate'))
    chk('退租原因含年审单号',
        '复核单' in str(t.get('exitReason')) or '年审' in str(t.get('exitReason')),
        t.get('exitReason'))
    chk('⭐ 给了 3 个月过渡期', str(t.get('transitionMonths')) == '3',
        t.get('transitionMonths'))
    chk('⭐ 过渡期租金倍率 1.5',
        abs(float(t.get('transitionRentMultiplier') or 0) - 1.5) < 1e-6,
        t.get('transitionRentMultiplier'))
    chk('过渡期起止日已生成', bool(t.get('transitionStartDate'))
        and bool(t.get('transitionEndDate')),
        (t.get('transitionStartDate'), t.get('transitionEndDate')))
    chk('初始状态 APPLYING/申请中', t.get('terminationStatus') == 'APPLYING',
        t.get('terminationStatus'))

# ---------- 3. 幂等：同合同已有退租单不重复发起 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID1, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2028', 'reviewType': 'SPECIAL'})
rid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid2, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid2, {'reviewResult': 'EXIT', 'adjustContent': '专项核查仍不达标'})
chk('再次 EXIT 年审完成', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=10&contractId=%s' % cid)
chk('⭐ 幂等：退租单仍只有 1 张', int((r.get('data') or {}).get('total', 0)) == 1,
    (r.get('data') or {}).get('total'))

# ---------- 4. 腾退单可正常走流程 ----------
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=5&contractId=%s' % cid)
tid = ((r.get('data') or {}).get('rows') or [{}])[0].get('id')
st, r = call('POST', '/api/v1/terminations/%s/submit' % tid, {})
chk('⭐ 自动生成的腾退单可提交审批',
    (r.get('data') or {}).get('terminationStatus') == 'APPROVING', r.get('code'))
st, r = call('POST', '/api/v1/terminations/%s/approve' % tid, {'reason': '同意退出'})
chk('可审批通过', (r.get('data') or {}).get('terminationStatus') == 'APPROVED', r.get('code'))

# ---------- 5. 无合同年审不报错 ----------
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID2, 'reviewYear': '2026', 'reviewType': 'DYNAMIC'})
rid3 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/annual-reviews/%s/start' % rid3, {})
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid3, {'reviewResult': 'EXIT', 'adjustContent': '动态核查不达标'})
chk('⭐ 无关联合同时 EXIT 不报错（跳过腾退）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
