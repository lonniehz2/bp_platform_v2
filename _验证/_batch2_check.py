# -*- coding: utf-8 -*-
"""本轮 9 项接口验证。"""
import json
import urllib.error
import urllib.request

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

# 1) 房源按组织筛选
st, r = call('/houses?pageNum=1&pageSize=1&orgId=370832680775979008')
print('1) 房源组织筛选:', st, 'total', (r.get('data') or {}).get('total'))

# 2) 轮候关键字 + 组织
st, r = call('/allocation/waiting?pageNum=1&pageSize=1&keyword=' + urllib.parse.quote('测试'))
print('2) 轮候关键字:', st, 'total', (r.get('data') or {}).get('total'))
st, r = call('/allocation/waiting?pageNum=1&pageSize=1&orgId=370832680775979008')
print('   轮候组织筛选:', st, 'total', (r.get('data') or {}).get('total'))

# 3) 批次组织筛选
st, r = call('/allocation/batches?pageNum=1&pageSize=5&orgId=371689292805836800')
rows = (r.get('data') or {}).get('rows') or []
print('3) 批次组织筛选:', st, 'total', (r.get('data') or {}).get('total'),
      '首条组织名:', rows[0].get('orgIdName') if rows else '-')

# 4) 批次重复发布（幂等）
draft = next((x for x in rows if x.get('batchStatus') == 'DRAFT'), None)
if draft:
    st1, r1 = call('/allocation/batches/%s/status' % draft['id'], 'POST',
                   {'batchStatus': 'PUBLISHED'})
    st2, r2 = call('/allocation/batches/%s/status' % draft['id'], 'POST',
                   {'batchStatus': 'PUBLISHED'})
    print('4) 发布两次:', st1, (r1.get('data') or {}).get('batchStatus'),
          '/', st2, (r2.get('data') or {}).get('batchStatus'),
          r2.get('message') or '')

# 5) 线下申请
st, r = call('/applications?pageNum=1&pageSize=5')
apps = (r.get('data') or {}).get('rows') or []
offline = [a for a in apps if a.get('applyChannel') == 'OFFLINE']
print('5) 线下申请:', len(offline), [(a.get('id'), a.get('applyStatus')) for a in offline[:2]])
