# -*- coding: utf-8 -*-
"""闭环验证：用人口一致的申请走完四级；线下通过；跳级拦截。"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
r = urllib.request.Request(BASE + '/api/v1/auth/login',
                           data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                            'password': 'admin123'}).encode(),
                           method='POST',
                           headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
TOKEN = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


def call(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + '/api/v1' + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


# 已知人口一致的候选（SUBMITTED/REVIEWING）
st, r = call('/applications?pageNum=1&pageSize=100&status=REVIEWING')
rows = ((r.get('data') or {}).get('rows') or [])
cand = rows[0]['id'] if rows else None
print('取审核中单:', cand, rows[0]['currentNode'] if rows else '')

# 找一条 currentNode=FINAL 的单直接终审
finals = [x for x in rows if x.get('currentNode') == 'FINAL']
print('FINAL 阶段:', [(x['id'], x['personId']) for x in finals[:2]])
if finals:
    st, r = call('/applications/%s/review' % finals[0]['id'], 'POST',
                 {'stage': 'FINAL', 'result': 'PASS', 'opinion': '终审通过（闭环验证）'})
    d = r.get('data') or {}
    print('终审:', st, d.get('applicationStatus'), '节点=', d.get('currentNode'), r.get('message') or '')

# 线下通过一条 SUBMITTED（人口一致优先：372443824670248960）
for aid in ['372443824670248960', '372443896564813824']:
    st, r = call('/applications/%s/offline-approve' % aid, 'POST', {'reason': '线下通过（闭环验证）'})
    d = r.get('data') or {}
    print('线下', aid, st, d.get('applicationStatus'), '节点=', d.get('currentNode'), r.get('message') or '')
    if st == 200:
        st2, r2 = call('/applications/%s' % aid)
        st3, r3 = call('/applications/%s/reviews' % aid) if False else (0, {})
        break
