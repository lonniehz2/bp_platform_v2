# -*- coding: utf-8 -*-
"""验证：新建批次 → 批次加房源 两个接口是否可用。"""
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
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


_, d = call('/auth/login', 'POST',
            {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = d['data']['token']

_, o = call('/orgs', token=tok)
orgs = ((o.get('data') or {}).get('rows') or [])
org = orgs[0]['id'] if isinstance(orgs, list) and orgs else None
print('组织:', org, (orgs[0].get('orgName') if isinstance(orgs, list) and orgs else ''))

st, b = call('/allocation/batches', 'POST',
             {'batchName': '联调测试批次', 'orgId': org,
              'securityType': 'PUBLIC', 'batchType': 'LOTTERY'}, tok)
print('新建批次:', st, (b or {}).get('code'), (b or {}).get('message', ''))
bid = ((b or {}).get('data') or {}).get('id')

if bid:
    st2, b2 = call('/allocation/batches/%s/houses' % bid, 'POST',
                   {'houseIds': ['1000000000000012161']}, tok)
    print('批次加房源:', st2, (b2 or {}).get('code'), (b2 or {}).get('message', ''))
    st3, b3 = call('/allocation/batches/%s/houses?pageNum=1&pageSize=10' % bid, token=tok)
    data3 = (b3 or {}).get('data') or {}
    print('批次内房源数:', len(data3.get('rows') or []), '总数:', data3.get('total'))
