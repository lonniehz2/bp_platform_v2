# -*- coding: utf-8 -*-
"""日房态与预订 · 验证（短租防超卖）"""
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
print(' 日房态与预订 · 短租防超卖验证')
print('=' * 74)

# ---------- 造房源 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'CT-' + sfx, 'orgName': '民宿验证',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')


def mkspace(parent, name, typ, code):
    b = {'orgId': int(org), 'spaceCode': code, 'spaceName': name, 'spaceType': typ}
    if parent:
        b['parentId'] = int(parent)
    st, rr = call('POST', '/api/v1/spaces', b)
    return (rr.get('data') or {}).get('id')


b = mkspace(None, 'A栋', 'BUILDING', 'AB-' + sfx)
u = mkspace(b, '1单元', 'UNIT', 'AU-' + sfx)
f = mkspace(u, '1层', 'FLOOR', 'AF-' + sfx)
room = mkspace(f, '8888', 'ROOM', 'AR-' + sfx)
st, r = call('POST', '/api/v1/houses', {'spaceId': int(room), 'houseCode': 'HT-' + sfx,
                                       'houseName': '8888民宿房', 'houseType': 'HOTEL',
                                       'area': '45'})
house = (r.get('data') or {}).get('id')
chk('建民宿房源', bool(house), house)

# ---------- 1. 铺月历 ----------
st, r = call('POST', '/api/v1/house-calendar/%s/ensure?month=2027-03' % house)
chk('⭐ 铺月历（2027-03）', r.get('code') == 'BP00000', r.get('code'))
chk('31 天全部补齐', int(r.get('data') or 0) == 31, r.get('data'))
st, r = call('POST', '/api/v1/house-calendar/%s/ensure?month=2027-03' % house)
chk('⭐ 铺月历幂等（重复补 0 天）', int(r.get('data') or 0) == 0, r.get('data'))

st, r = call('GET', '/api/v1/house-calendar/%s?month=2027-03' % house)
cells = r.get('data') or []
chk('月历返回 31 天', len(cells) == 31, len(cells))
chk('初始全部可售', all(c.get('dayStatus') == 'AVAILABLE' for c in cells),
    set(c.get('dayStatus') for c in cells))
chk('房态标签=可售', cells[0].get('dayStatusLabel') == '可售', cells[0].get('dayStatusLabel'))

# ---------- 2. 可售查询 ----------
st, r = call('GET', '/api/v1/house-calendar/%s/availability?checkIn=2027-03-10&checkOut=2027-03-13'
             % house)
av = r.get('data') or {}
chk('⭐ 区间 [3-10, 3-13) = 3 天', str(av.get('days')) == '3', av.get('days'))
chk('整段可售 available=true', av.get('available') in (True, 'true'), av.get('available'))

# ---------- 3. 预订（左闭右开）----------
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-10', 'checkOut': '2027-03-13',
    'bookingId': 88001, 'sourceType': 'BOOKING', 'targetStatus': 'BOOKED',
    'remark': '张三预订'})
chk('⭐ 预订成功，占 3 天', int(r.get('data') or 0) == 3,
    str(r.get('code')) + ' ' + str(r.get('data')))

st, r = call('GET', '/api/v1/house-calendar/%s?month=2027-03' % house)
cells = {c.get('date'): c for c in (r.get('data') or [])}
chk('⭐ 3-10/11/12 为已预订',
    all(cells.get(d, {}).get('dayStatus') == 'BOOKED'
        for d in ('2027-03-10', '2027-03-11', '2027-03-12')),
    {d: cells.get(d, {}).get('dayStatus') for d in
     ('2027-03-10', '2027-03-11', '2027-03-12')})
chk('⭐ 3-13 仍可售（右开区间）',
    cells.get('2027-03-13', {}).get('dayStatus') == 'AVAILABLE',
    cells.get('2027-03-13', {}).get('dayStatus'))
chk('占用单据已记录', str(cells.get('2027-03-10', {}).get('bookingId')) == '88001',
    cells.get('2027-03-10', {}).get('bookingId'))

# ---------- 4. 防超卖（核心）----------
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-11', 'checkOut': '2027-03-14',
    'bookingId': 88002, 'sourceType': 'BOOKING'})
chk('⭐ 完全重叠被拒（防超卖）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝原因：%s' % r.get('message'))

st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-09', 'checkOut': '2027-03-11',
    'bookingId': 88003, 'sourceType': 'BOOKING'})
chk('⭐ 部分重叠也整单拒绝', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('GET', '/api/v1/house-calendar/%s/availability?checkIn=2027-03-11&checkOut=2027-03-13'
             % house)
chk('被占区间 available=false',
    (r.get('data') or {}).get('available') in (False, 'false'),
    (r.get('data') or {}).get('available'))
chk('可售天数 0', str((r.get('data') or {}).get('freeDays')) == '0',
    (r.get('data') or {}).get('freeDays'))

st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-13', 'checkOut': '2027-03-15',
    'bookingId': 88004, 'sourceType': 'BOOKING'})
chk('⭐ 紧邻区间可预订（3-13 未被占）', int(r.get('data') or 0) == 2,
    str(r.get('code')) + ' ' + str(r.get('data')))

# ---------- 5. 释放（按 bookingId 匹配）----------
st, r = call('POST', '/api/v1/house-calendar/release', {
    'houseId': int(house), 'checkIn': '2027-03-10', 'checkOut': '2027-03-13',
    'bookingId': 99999})
chk('⭐ 单据不匹配不释放（防误放）', int(r.get('data') or 0) == 0, r.get('data'))

st, r = call('POST', '/api/v1/house-calendar/release', {
    'houseId': int(house), 'checkIn': '2027-03-10', 'checkOut': '2027-03-13',
    'bookingId': 88001})
chk('⭐ 匹配单据正确释放 3 天', int(r.get('data') or 0) == 3, r.get('data'))
st, r = call('GET', '/api/v1/house-calendar/%s?month=2027-03' % house)
cells = {c.get('date'): c for c in (r.get('data') or [])}
chk('释放后 3-10 恢复可售',
    cells.get('2027-03-10', {}).get('dayStatus') == 'AVAILABLE',
    cells.get('2027-03-10', {}).get('dayStatus'))

# ---------- 6. 停售 / 维修 ----------
st, r = call('POST', '/api/v1/house-calendar/%s/status' % house, {
    'start': '2027-03-20', 'end': '2027-03-22', 'dayStatus': 'MAINTENANCE',
    'remark': '空调维修'})
chk('⭐ 设置维修 3 天', int(r.get('data') or 0) == 3, r.get('data'))
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-21', 'checkOut': '2027-03-23',
    'bookingId': 88005, 'sourceType': 'BOOKING'})
chk('⭐ 维修期间不可预订', r.get('code') == 'BP40001', r.get('code'))

st, r = call('POST', '/api/v1/house-calendar/%s/status' % house, {
    'start': '2027-03-25', 'end': '2027-03-26', 'dayStatus': 'BOOKED'})
chk('占用类房态不可手工设置', r.get('code') == 'BP10001', r.get('code'))

# ---------- 7. 当日调价 ----------
st, r = call('POST', '/api/v1/house-calendar/%s/price' % house, {
    'date': '2027-03-08', 'price': '588.00'})
chk('⭐ 当日调价（节假日）', str((r.get('data') or {}).get('price')) == '588.00',
    (r.get('data') or {}).get('price'))
st, r = call('POST', '/api/v1/house-calendar/%s/price' % house, {
    'date': '2027-03-08', 'price': '-1'})
chk('负价被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 8. 区间校验 ----------
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-15', 'checkOut': '2027-03-15',
    'bookingId': 88006})
chk('⭐ 退房日必须晚于入住日', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': int(house), 'checkIn': '2027-03-15', 'checkOut': '2027-03-10',
    'bookingId': 88007})
chk('退房早于入住被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/house-calendar/book', {
    'houseId': 999999999, 'checkIn': '2027-03-15', 'checkOut': '2027-03-16'})
chk('房源不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

# ---------- 9. 搜可售房 ----------
st, r = call('GET', '/api/v1/house-calendar/available?orgId=%s&checkIn=2027-03-01&checkOut=2027-03-05'
             % org)
chk('⭐ 整段可售房源搜索', r.get('code') == 'BP00000', r.get('code'))
found = [x for x in (r.get('data') or []) if str(x.get('houseId')) == str(house)]
chk('搜到本房源（3-01~3-05 未占用）', len(found) >= 1, len(r.get('data') or []))

print()
print('-' * 74)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 74)
