# -*- coding: utf-8 -*-
"""四级审批闭环：受理 → 四级 → 通过；跳级拦截；线下一次通过。"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'


def login():
    req = urllib.request.Request(BASE + '/api/v1/auth/login',
                                 data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                                  'password': 'admin123'}).encode(),
                                 method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['token']


TOKEN = login()


def call(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + '/api/v1' + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


st, r = call('/applications?pageNum=1&pageSize=5&status=SUBMITTED')
rows = ((r.get('data') or {}).get('rows') or [])
print('待受理单数:', (r.get('data') or {}).get('total'), [x['id'] for x in rows][:3])

if rows:
    aid = rows[0]['id']
    st, r = call('/applications/%s/accept' % aid, 'POST', {})
    d = r.get('data') or {}
    print('1) 受理:', st, d.get('applicationStatus'), '节点=', d.get('currentNode'), r.get('message') or '')

    st, r = call('/applications/%s/review' % aid, 'POST',
                 {'stage': 'FINAL', 'result': 'PASS', 'opinion': '跳级测试'})
    print('2) 跳级 FINAL:', st, r.get('message'))

    for stage in ['ACCEPT', 'FORM', 'JOINT', 'FINAL']:
        st, r = call('/applications/%s/review' % aid, 'POST',
                     {'stage': stage, 'result': 'PASS', 'opinion': '闭环验证 ' + stage})
        d = r.get('data') or {}
        print('3) %-5s →' % stage, st, d.get('applicationStatus'), '节点=', d.get('currentNode'),
              '' if st == 200 else r.get('message'))

# 线下一次通过
st, r = call('/applications?pageNum=1&pageSize=5&status=SUBMITTED')
rows2 = ((r.get('data') or {}).get('rows') or [])
if rows2:
    aid2 = rows2[0]['id']
    st, r = call('/applications/%s/offline-approve' % aid2, 'POST',
                 {'reason': '线下渠道受理通过（闭环验证）'})
    d = r.get('data') or {}
    print('4) 线下通过:', st, d.get('applicationStatus'), '节点=', d.get('currentNode'),
          r.get('message') or '')
