# -*- coding: utf-8 -*-
"""验证管理权转移规则：
  1. 管理员（所有权方）可授予 MANAGEMENT
  2. 仅持 MANAGEMENT 者不能再转移 → 拒绝并提示"只能归还"
  3. 持有者可归还自己的管理权（revoke 放行）
"""
import json
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

B = 'http://192.168.31.11:8080/api/v1'


def call(p, m='GET', body=None, tok=None):
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login(u, p):
    r = urllib.request.Request(
        B + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': u, 'password': p}).encode(),
        method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())['data']['token']


admin = login('admin', 'admin123')
contract = login('test_asset', 'Test@1234')

st, r = call('/auth/me', tok=contract)
me = (r or {}).get('data') or {}
print('/auth/me:', st, 'personId =', me.get('personId'), 'admin =', me.get('admin'))

hs = (call('/houses?pageNum=1&pageSize=1', tok=admin)[1] or {}).get('data', {}).get('rows') or []
sp = hs[0]['spaceId']
person_id = me.get('personId') or me.get('userId')
print('空间:', sp, ' 目标人员:', person_id)

start = str(date.today()) + ' %02d:%02d:00' % (int(time.time()) % 24, int(time.time()) % 60)
end = str(date.today() + timedelta(days=60)) + ' 23:59:59'

st, r = call('/grants', 'POST', {
    'personId': person_id, 'spaceId': sp, 'grantLevel': 'MANAGEMENT',
    'validStart': start, 'validEnd': end}, admin)
g = (r or {}).get('data') or {}
print('1) 管理员授予 MANAGEMENT:', st, (r or {}).get('code'), g.get('grantNo'),
      (r or {}).get('message', '')[:40])

st2, r2 = call('/grants', 'POST', {
    'personId': person_id, 'spaceId': sp, 'grantLevel': 'MANAGEMENT',
    'validStart': start, 'validEnd': end}, contract)
print('2) 管理权持有者再转移:', st2, (r2 or {}).get('code'),
      (r2 or {}).get('message', '')[:60])

if g.get('id'):
    st3, r3 = call('/grants/%s/revoke' % g['id'], 'POST',
                   {'reason': '持有人归还管理权'}, contract)
    print('3) 持有人归还自己的管理权:', st3, (r3 or {}).get('code'),
          (r3 or {}).get('message', '')[:50])
