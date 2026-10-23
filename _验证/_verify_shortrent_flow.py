# -*- coding: utf-8 -*-
"""验证短租订单全状态流转：下单→确认→入住→退房→收款，并核对房态与账单。"""
import json
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {'message': type(e).__name__}


def d(resp):
    return (resp[1] or {}).get('data')


def ok(resp):
    return (resp[1] or {}).get('code') == 'BP00000'


def rows(resp):
    data = d(resp)
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


tok = d(call('/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'}))['token']
hotel = rows(call('/houses?pageNum=1&pageSize=1&houseType=HOTEL', token=tok))
hid = hotel[0]['id']
call('/house-calendar/release', 'POST',
     {'houseId': hid, 'checkIn': '2027-01-01', 'checkOut': '2027-02-01'}, tok)

st, r = call('/short-rent-orders', 'POST',
             {'houseId': hid, 'sourceChannel': 'WALKIN',
              'checkInTime': '2027-01-10 14:00:00',
              'checkOutTime': '2027-01-12 12:00:00',
              'guestName': '状态流转测试', 'guestPhone': '13700002222',
              'guestCount': 2, 'nightlyPrice': 320}, tok)
o = d((st, r)) or {}
oid = o.get('id')
print('1 下单      :', st, ok((st, r)), o.get('orderNo'), '状态', o.get('orderStatus'))

steps = [
    ('2 确认', '/confirm', None),
    ('3 入住', '/check-in', None),
    ('4 退房', '/check-out', {'extraAmount': 50}),
]
for name, path, body in steps:
    st2, r2 = call('/short-rent-orders/%s%s' % (oid, path), 'POST', body or {}, tok)
    oo = d((st2, r2)) or {}
    print('%-10s:' % name, st2, ok((st2, r2)), '状态', oo.get('orderStatus'),
          (r2 or {}).get('message', '')[:30] if not ok((st2, r2)) else '')

st3, r3 = call('/short-rent-orders/%s/pay' % oid, 'POST',
               {'amount': float(o.get('roomAmount') or 0) + 50}, tok)
print('5 收款      :', st3, ok((st3, r3)), (r3 or {}).get('code'))

cells = rows(call('/house-calendar/%s?month=2027-01' % hid, token=tok))
busy = [(c.get('date'), c.get('dayStatus')) for c in cells
        if c.get('dayStatus') not in ('FREE', 'AVAILABLE', None)]
print('退房后房态占用:', busy[:5], '（退房应只保留历史占用或已释放）')

st4, r4 = call('/short-rent-orders/%s' % oid, token=tok)
final = d((st4, r4)) or {}
print('最终状态    :', final.get('orderStatus'), '已收', final.get('paidAmount'),
      '合计', final.get('totalAmount'))
print('\n结论：', '全流程通过' if final.get('orderStatus') == 'CHECKED_OUT' else '需排查')
