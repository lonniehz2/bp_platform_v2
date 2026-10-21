# -*- coding: utf-8 -*-
"""验证：签约强制校验配租公示（合规闭环）"""
import datetime
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
print(' 配租公示 → 签约 强制校验（合规闭环验证）')
print('=' * 78)

# ---------- 准备：独立组织（避免历史公示干扰）----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'GT-' + sfx, 'orgName': '公示拦截验证小区',
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
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'GTH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')

# 轮候 1 人
st, r = call('POST', '/api/v1/allocation/waiting', {
    'personId': 7001, 'applicationId': 8701 + int(sfx), 'securityType': 'PUBLIC',
    'orgId': int(org), 'priorityScore': '0'})
chk('入轮候', r.get('code') == 'BP00000', r.get('code'))

# 建批次 + 发布 + 报名 + 摇号
st, r = call('POST', '/api/v1/allocation/batches', {
    'batchName': '公示拦截验证批次', 'orgId': int(org), 'securityType': 'PUBLIC',
    'batchType': 'LOTTERY', 'houseIds': [int(house)]})
bid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'PUBLISHED'})
call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'SIGNUP'})
st, r = call('POST', '/api/v1/allocation/lottery', {'batchId': int(bid), 'seed': 'GT-SEED'})
res = r.get('data') or []
won = [x for x in res if x.get('resultType') == 'WON']
chk('⭐ 摇号产生中签', len(won) == 1, len(res))

# ---------- 1. ⭐ 未公示 → 签约被拦截（核心）----------
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(house), 'personId': 7001,
    'lotteryResultId': int(won[0].get('id'))})
chk('生成配租单（配租本身不拦）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
aid = (r.get('data') or {}).get('id')

st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid, {})
chk('⭐⭐ 未公示 → 签约被强制拦截', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拦截信息：%s' % r.get('message'))
chk('拦截信息含"公示"', '公示' in str(r.get('message')), r.get('message'))
chk('拦截信息含"7"', '7' in str(r.get('message')), r.get('message'))

# 确认状态仍是待签约（未误改）
st, r = call('GET', '/api/v1/allocation/allocations/%s' % aid)
chk('⭐ 拦截后配租单仍为待签约',
    (r.get('data') or {}).get('allocationStatus') == 'PENDING_SIGN',
    (r.get('data') or {}).get('allocationStatus'))

# ---------- 2. 公示只有草稿（未结束）→ 仍拦截 ----------
d0 = datetime.date.today()
d6 = d0 + datetime.timedelta(days=6)
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': int(org), 'title': '配租结果公示（草稿）',
    'startDate': d0.isoformat(), 'endDate': d6.isoformat()})
pubId = (r.get('data') or {}).get('id')
chk('建配租公示（草稿）', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid, {})
chk('⭐ 仅草稿公示 → 仍拦截', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 3. 公示已发布但未结束 → 仍拦截 ----------
st, r = call('POST', '/api/v1/publicities/%s/publish' % pubId, {})
chk('发布公示', (r.get('data') or {}).get('publicityStatus') == 'PUBLISHED', r.get('code'))
st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid, {})
chk('⭐ 公示进行中（未结束）→ 仍拦截', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 4. 公示结束 → 签约放行 ----------
st, r = call('POST', '/api/v1/publicities/%s/close' % pubId, {'remark': '公示期满无异议'})
chk('结束公示', (r.get('data') or {}).get('publicityStatus') == 'CLOSED', r.get('code'))

st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid, {})
chk('⭐⭐ 公示已结束 → 签约放行', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
chk('状态 SIGNED/已签约', (r.get('data') or {}).get('allocationStatus') == 'SIGNED',
    (r.get('data') or {}).get('allocationStatus'))

# ---------- 5. 房源池置已选中 ----------
st, r = call('GET', '/api/v1/allocation/batches/%s/houses?inPoolStatus=SELECTED' % bid)
chk('⭐ 房源池 SELECTED', len(r.get('data') or []) == 1, r.get('data'))

# ---------- 6. 其他组织未公示 → 互不影响 ----------
st, r = call('GET', '/api/v1/publicities/allocation-check?orgId=%s' % org)
chk('本组织公示检查 = true', r.get('data') in (True, 'true'), r.get('data'))
st, r = call('GET', '/api/v1/publicities/allocation-check?orgId=999999999')
chk('⭐ 无公示组织的检查 = false（隔离）', r.get('data') in (False, 'false'), r.get('data'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
