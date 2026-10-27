# -*- coding: utf-8 -*-
"""验证：人工核验通过、轮候入队、公示 allocation-check、空间树。"""
import json
import urllib.error
import urllib.request

import pymysql

BASE = 'http://192.168.31.11:8080'
TOKEN = None


def call(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + '/api/v1' + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + (TOKEN or '')})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login():
    global TOKEN
    req = urllib.request.Request(BASE + '/api/v1/auth/login',
                                 data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                                  'password': 'admin123'}).encode(),
                                 method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    TOKEN = json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['token']


login()

# 1) 人工核验通过
st, r = call('/persons?pageNum=1&pageSize=1&verifyStatus=UNVERIFIED')
person = ((r.get('data') or {}).get('rows') or [{}])[0]
pid = person.get('id')
print('待核验人员:', pid, person.get('personName'), person.get('verifyStatus'))
if pid:
    st, r = call('/verify-records', 'POST', {
        'personId': pid, 'verifyType': 'MANUAL', 'faceResult': '1',
        'citizenResult': '0', 'responseCode': '0', 'resultCode': '0', 'faceScore': 100,
        'rawResponse': '{"source":"manual-demo"}'})
    rec = r.get('data') or {}
    print('1) 人工核验:', st, 'verifyPass=', rec.get('verifyPass'))
    st, r = call('/persons/%s' % pid)
    print('   人员实名状态:', (r.get('data') or {}).get('verifyStatus'))

# 2) 已通过申请单 → 入队
st, r = call('/applications?status=APPROVED&pageNum=1&pageSize=1')
app = ((r.get('data') or {}).get('rows') or [{}])[0]
print('2) 已通过申请:', app.get('id'), 'person=', app.get('personId'),
      'org=', app.get('orgId'), '类型=', app.get('securityType'))
if app.get('id'):
    st, r = call('/allocation/waiting', 'POST', {
        'personId': app.get('personId'), 'applicationId': app.get('id'),
        'securityType': app.get('securityType') or 'PUBLIC', 'orgId': app.get('orgId'),
        'priorityScore': 0})
    print('   入队:', st, (r.get('data') or {}).get('waitingNo') or r.get('message'))

# 3) 公示 allocation-check 不再报“参数类型错误”
st, r = call('/publicities/allocation-check?orgId=%s' % (app.get('orgId') or ''))
print('3) 公示校验:', st, r.get('data'), r.get('message') or '')

# 4) 空间树
st, r = call('/orgs?pageNum=1&pageSize=1')
org = ((r.get('data') or {}).get('rows') or [{}])[0]
st, r = call('/spaces/tree?orgId=%s' % org.get('id'))
tree = r.get('data') or []
print('4) 空间树:', st, '组织', org.get('orgName'), '根节点数', len(tree))
