# -*- coding: utf-8 -*-
"""按真实枚举与字段修正日房态示例"""
import io
import json
import urllib.error
import urllib.request

P = r'D:\Work\业务平台开发\frontend\src\views\OpsExtras.vue'
s = io.open(P, encoding='utf-8').read()

FIX = [
    ("""    { start: '2026-11-01', end: '2026-11-01', dayStatus: 'LOCKED',
      remark: '手动锁定' })""",
     """    { start: '2026-11-01', end: '2026-11-01', dayStatus: 'MAINTENANCE',
      remark: '维修停用' })"""),
    ("""  openJson('修改日房态', 'dayStatus：FREE / FULL / LOCKED / CLOSED',""",
     """  openJson('修改日房态', 'dayStatus：AVAILABLE / BOOKED / OCCUPIED / CLOSED / MAINTENANCE',"""),
    ("""    { houseId: 1, start: '2026-11-01', end: '2026-11-03',
      orderId: 1, remark: '预订占用' })""",
     """    { houseId: 1, checkIn: '2026-11-01', checkOut: '2026-11-03',
      bookingId: 1, guestName: '客人' })"""),
    ("""    { houseId: 1, start: '2026-11-01', end: '2026-11-03' })""",
     """    { houseId: 1, checkIn: '2026-11-01', checkOut: '2026-11-03',
      bookingId: 1 })"""),
]
n = 0
for old, new in FIX:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1
io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 修正 %d 处' % n)

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
HOUSE = (D.get('houses') or [None])[0]


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
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

print('\n复验：')
st, r = call('POST', '/api/v1/house-calendar/%s/status' % HOUSE,
             {'start': '2026-12-01', 'end': '2026-12-01',
              'dayStatus': 'MAINTENANCE', 'remark': '维修停用'}, TOK)
print('  改状态：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:44]))
st, r = call('POST', '/api/v1/house-calendar/book',
             {'houseId': HOUSE, 'checkIn': '2026-12-05', 'checkOut': '2026-12-07',
              'bookingId': 1, 'guestName': '客人'}, TOK)
print('  预订：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:44]))
st, r = call('POST', '/api/v1/house-calendar/release',
             {'houseId': HOUSE, 'checkIn': '2026-12-05', 'checkOut': '2026-12-07',
              'bookingId': 1}, TOK)
print('  释放：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:44]))
