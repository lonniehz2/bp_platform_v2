# -*- coding: utf-8 -*-
"""四级审批闭环验证：受理 → 四级 → 通过；跳级被拦；线下一次通过。"""
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


# 1) 找 SUBMITTED 受理
st, r = call('/applications?pageNum=1&pageSize=1&applicationStatus=SUBMITTED')
app = ((r.get('data') or {}).get('rows') or [None])[0]
print('1) 待受理:', app and app['id'], app and app['applicationStatus'])
aid = app['id']
st, r = call('/applications/%s/accept' % aid, 'POST', {})
print('   受理:', st, (r.get('data') or {}).get('applicationStatus'),
      '节点=', (r.get('data') or {}).get('currentNode'))

# 2) 跳级：直接 FINAL 应被拦
st, r = call('/applications/%s/review' % aid, 'POST',
             {'stage': 'FINAL', 'result': 'PASS', 'opinion': '跳级测试'})
print('2) 跳级 FINAL:', st, r.get('message'))

# 3) 逐级通过
for stage in ['ACCEPT', 'FORM', 'JOINT', 'FINAL']:
    st, r = call('/applications/%s/review' % aid, 'POST',
                 {'stage': stage, 'result': 'PASS', 'opinion': '闭环验证 ' + stage})
    d = r.get('data') or {}
    print('   %-5s →' % stage, st, d.get('applicationStatus'), '节点=', d.get('currentNode'),
          r.get('message') if st != 200 else '')

# 4) 线下一次通过（取另一单）
st, r = call('/applications?pageNum=1&pageSize=1&applicationStatus=SUBMITTED')
app2 = ((r.get('data') or {}).get('rows') or [None])[0]
print('4) 线下通过单:', app2 and app2['id'])
if app2:
    st, r = call('/applications/%s/offline-approve' % app2['id'], 'POST',
                 {'reason': '线下渠道受理通过（闭环验证）'})
    d = r.get('data') or {}
    print('   结果:', st, d.get('applicationStatus'), '节点=', d.get('currentNode'), r.get('message') or '')

# 5) 轨迹阶段
st, r = call('/applications/%s' % aid)
print('5) 单号', (r.get('data') or {}).get('applicationNo'), '状态', (r.get('data') or {}).get('applicationStatus'))
