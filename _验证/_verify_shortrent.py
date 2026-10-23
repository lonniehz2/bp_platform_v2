# -*- coding: utf-8 -*-
"""验证短租订单 ↔ 日房态联动：下单占房、取消释放。"""
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


def rows(resp):
    data = (resp[1] or {}).get('data')
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


def busy_cells(token, house_id, month):
    cells = rows(call('/house-calendar/%s?month=%s' % (house_id, month), token=token))
    return [(c.get('date'), c.get('dayStatus')) for c in cells
            if c.get('dayStatus') not in ('FREE', 'AVAILABLE', None)]


tok = (call('/auth/login', 'POST',
            {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})[1]
       ['data']['token'])
hotel = rows(call('/houses?pageNum=1&pageSize=1&houseType=HOTEL', token=tok))
if not hotel:
    print('无酒店房源')
    raise SystemExit(1)
hid = hotel[0]['id']

# 先清空 11 月房态，保证可复现
call('/house-calendar/release', 'POST',
     {'houseId': hid, 'checkIn': '2026-11-01', 'checkOut': '2026-12-01'}, tok)
print('初始占用：', busy_cells(tok, hid, '2026-11'))

st, r = call('/short-rent-orders', 'POST',
             {'houseId': hid, 'sourceChannel': 'DIRECT',
              'checkInTime': '2026-11-05 14:00:00',
              'checkOutTime': '2026-11-08 12:00:00',
              'guestName': '联动测试客人', 'guestPhone': '13900001111',
              'guestCount': 2, 'nightlyPrice': 300}, tok)
o = (r or {}).get('data') or {}
print('建订单：%s %s  单号=%s 晚数=%s 金额=%s'
      % (st, (r or {}).get('code'), o.get('orderNo'), o.get('nightCount'),
         o.get('roomAmount')))
after_book = busy_cells(tok, hid, '2026-11')
print('下单后占用：', after_book[:6])

if o.get('id'):
    st2, r2 = call('/short-rent-orders/%s/cancel' % o['id'], 'POST',
                   {'reason': '联调取消'}, tok)
    after_cancel = busy_cells(tok, hid, '2026-11')
    print('取消订单：%s %s → 剩余占用 %d 天'
          % (st2, (r2 or {}).get('code'), len(after_cancel)))

print('\n结论：', '联调通过' if o.get('id') and len(after_book) == 3 else '需排查')
