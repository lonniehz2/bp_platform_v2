# -*- coding: utf-8 -*-
"""查 nightlyPrice 与 grantLevel 枚举后正确造数"""
import io
import json
import os
import re
import urllib.error
import urllib.request

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
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


# 找 grantLevel 与 nightlyPrice 的约束
for name in ('GrantCreateCmd', 'GrantEntitlement', 'ShortRentCreateCmd',
             'ShortRentOrderCreateCmd'):
    found = False
    for root, _, files in os.walk(JAVA):
        if name + '.java' not in files:
            continue
        s = io.open(os.path.join(root, name + '.java'), encoding='utf-8').read()
        m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
        if m:
            body = re.sub(r'\s+', ' ', re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S))
            print('■ %s：%s' % (name, body[:520]))
            found = True
            break
    if not found:
        print('□ %s 未找到' % name)

TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('\n■ 造数')
st, r = call('POST', '/api/v1/short-rent-orders', {
    'houseId': HOUSE, 'spaceId': ROOM, 'sourceChannel': 'DIRECT',
    'guestName': '短租客人1', 'guestPhone': '13900139001',
    'guestIdCard': '350600199001011231', 'guestCount': 2,
    'checkInTime': '2026-11-10 14:00:00', 'checkOutTime': '2026-11-13 12:00:00',
    'nightCount': 3, 'nightlyPrice': 200, 'totalAmount': 600,
    'depositAmount': 200, 'remark': '自动测试'})
print('  短租：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:70]))

for lvl in ('DOOR', 'HOUSE', 'BUILDING', 'COMMUNITY', 'ALL'):
    st, r = call('POST', '/api/v1/grants', {
        'personId': PERSON, 'spaceId': ROOM, 'grantLevel': lvl,
        'validStart': '2026-11-01 00:00:00', 'validEnd': '2026-12-31 23:59:59',
        'sourceType': 'CONTRACT', 'sourceId': D['contracts'][0]['id'],
        'remark': '自动测试'})
    print('  授权 %-10s %s %s' % (lvl, r.get('code'), str(r.get('message'))[:56]))
    if r.get('code') == 'BP00000':
        break
