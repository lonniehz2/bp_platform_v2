# -*- coding: utf-8 -*-
"""用正确枚举 OWNERSHIP|MANAGEMENT|USAGE|VISIT 造通行授权"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
PERSON = D['persons'][0]
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

print('■ 通行授权（OWNERSHIP/MANAGEMENT/USAGE/VISIT）')
for lvl in ('USAGE', 'MANAGEMENT'):
    st, r = call('POST', '/api/v1/grants', {
        'personId': PERSON, 'spaceId': ROOM, 'grantLevel': lvl,
        'validStart': '2026-11-01 00:00:00', 'validEnd': '2026-12-31 23:59:59',
        'sourceType': 'CONTRACT', 'sourceId': D['contracts'][0]['id'],
        'remark': '自动测试授权'})
    print('  %-11s %s %s %s' % (lvl, st, r.get('code'),
                                str(r.get('message'))[:56]))
    if r.get('code') == 'BP00000':
        break

for name, path in (('短租', '/short-rent-orders'), ('授权', '/grants'),
                   ('退租', '/terminations')):
    st, r = call('GET', '%s?pageNum=1&pageSize=5' % ('/api/v1' + path))
    d = r.get('data') or {}
    t = d.get('total')
    print('  %-4s %s 条' % (name, int(t) if t not in (None, '') else 0))
