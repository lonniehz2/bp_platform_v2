# -*- coding: utf-8 -*-
"""补验：递补人员具备配租资格 + 轮候队列一致性"""
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


def chk(n, c, e=''):
    global ok, fail
    if c:
        ok += 1
        print('  [PASS] ' + n)
    else:
        fail += 1
        print('  [FAIL] ' + n + '  ' + str(e))


sfx = str(int(time.time()))[-6:]
print('=== 补验：递补资格 + 放弃后补位 ===')

st, r = call('POST', '/api/v1/orgs', {'orgCode': 'WL-' + sfx, 'orgName': '递补验证',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'spaceCode': 'WLB-' + sfx,
                                       'spaceName': '1幢', 'spaceType': 'BUILDING'})
bd = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(bd),
                                       'spaceCode': 'WLU-' + sfx, 'spaceName': '1单元',
                                       'spaceType': 'UNIT'})
un = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(un),
                                       'spaceCode': 'WLF-' + sfx, 'spaceName': '1层',
                                       'spaceType': 'FLOOR'})
fl = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(fl),
                                       'spaceCode': 'WLR-' + sfx, 'spaceName': '101',
                                       'spaceType': 'ROOM', 'area': '80'})
rm = (r.get('data') or {}).get('id')
assert rm, '建房失败: %s' % r
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'WLH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')

# 1 套房源 + 2 人 → 1 中签 1 递补
for pid, appid, pri in ((5001, 8501, '0'), (5002, 8502, '0')):
    call('POST', '/api/v1/allocation/waiting', {
        'personId': pid, 'applicationId': appid + int(sfx), 'securityType': 'PUBLIC',
        'orgId': int(org), 'priorityScore': pri})

st, r = call('POST', '/api/v1/allocation/batches', {
    'batchName': '递补验证批次', 'orgId': int(org), 'securityType': 'PUBLIC',
    'batchType': 'LOTTERY', 'houseIds': [int(house)]})
bid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'PUBLISHED'})
call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'SIGNUP'})
st, r = call('POST', '/api/v1/allocation/lottery', {'batchId': int(bid), 'seed': 'S1'})
res = r.get('data') or []
won = [x for x in res if x.get('resultType') == 'WON']
wl = [x for x in res if x.get('resultType') == 'WAITLIST']
print('     结果：%s' % [(x.get('personId'), x.get('resultTypeLabel')) for x in res])
chk('⭐ 1 中签', len(won) == 1, len(won))
chk('⭐ 1 递补', len(wl) == 1, len(wl))

# 中签者配租后放弃 → 房源回池
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(house), 'personId': int(won[0].get('personId')),
    'lotteryResultId': int(won[0].get('id'))})
aid = (r.get('data') or {}).get('id')
chk('中签者生成配租单', bool(aid), aid)
st, r = call('POST', '/api/v1/allocation/allocations/%s/give-up' % aid, {'reason': '放弃'})
chk('放弃 → 房源回池', (r.get('data') or {}).get('allocationStatus') == 'CANCELLED', r.get('code'))
st, r = call('GET', '/api/v1/allocation/batches/%s/houses?inPoolStatus=AVAILABLE' % bid)
chk('⭐ 房源已回池可再次配租', len(r.get('data') or []) == 1, r.get('data'))

# 递补人员配租（canAllocate: WON/WAITLIST 均可）
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(house), 'personId': int(wl[0].get('personId')),
    'lotteryResultId': int(wl[0].get('id'))})
chk('⭐ 递补人员可配租（补位成功）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
if r.get('code') == 'BP00000':
    st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % (r.get('data') or {}).get('id'), {})
    chk('递补者签约成功', (r.get('data') or {}).get('allocationStatus') == 'SIGNED', r.get('code'))

print()
print('  通过 %d / 失败 %d' % (ok, fail))
