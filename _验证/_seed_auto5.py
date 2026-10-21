# -*- coding: utf-8 -*-
"""修正时间字段：短租订单、通行授权"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
PERSON = D['persons'][0]
HOUSE = (D.get('houses') or [None])[0]
ROOMS = [r for r in D.get('rooms', []) if r]
ROOM = ROOMS[0] if ROOMS else None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('■ 短租订单（checkIn < checkOut）')
for i, (ci, co) in enumerate((('2026-11-10 14:00:00', '2026-11-13 12:00:00'),
                              ('2026-11-20 15:00:00', '2026-11-22 11:00:00')), 1):
    st, r = call('POST', '/api/v1/short-rent-orders', {
        'houseId': HOUSE, 'spaceId': ROOM, 'sourceChannel': 'DIRECT',
        'guestName': '短租客人%d' % i, 'guestPhone': '1390013900%d' % i,
        'guestIdCard': '35060019900101123%d' % i, 'guestCount': 2,
        'checkInTime': ci, 'checkOutTime': co, 'nightCount': 3,
        'roomRate': 200, 'totalAmount': 600, 'depositAmount': 200,
        'remark': '自动测试'})
    print('  %s %s %s' % (st, r.get('code'), str(r.get('message'))[:64]))

print('\n■ 通行授权（validStart < validEnd）')
st, r = call('POST', '/api/v1/grants', {
    'personId': PERSON, 'spaceId': ROOM, 'grantLevel': 'PASSAGE',
    'validStart': '2026-11-01 00:00:00', 'validEnd': '2026-12-31 23:59:59',
    'sourceType': 'CONTRACT', 'sourceId': D['contracts'][0]['id'],
    'remark': '自动测试授权'})
print('  %s %s %s' % (st, r.get('code'), str(r.get('message'))[:64]))

for name, path in (('短租', '/api/v1/short-rent-orders?pageNum=1&pageSize=5'),
                   ('授权', '/api/v1/grants?pageNum=1&pageSize=5'),
                   ('退租', '/api/v1/terminations?pageNum=1&pageSize=5')):
    st, r = call('GET', path)
    d = r.get('data') or {}
    t = d.get('total')
    print('  %-4s %s 条' % (name, int(t) if t not in (None, '') else 0))
