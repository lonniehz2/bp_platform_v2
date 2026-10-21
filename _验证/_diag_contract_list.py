# -*- coding: utf-8 -*-
"""确认合同列表排序 / 是否支持 keyword"""
import json
import urllib.request

BASE = 'http://192.168.31.11:8080'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Tenant-Id', '350600')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


st, d = call('/api/v1/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = (d.get('data') or {}).get('token')

st, cd = call('/api/v1/contracts?pageNum=1&pageSize=5', 'GET', None, tok)
rows = ((cd.get('data') or {}).get('rows') or [])
print('合同 total=', (cd.get('data') or {}).get('total'))
print('首页合同号/状态/创建时间：')
for r in rows:
    print('  ', r.get('contractNo'), r.get('contractStatus'), r.get('createTime'))

print('\n按 keyword 过滤（应为新合同）：')
st, kd = call('/api/v1/contracts?pageNum=1&pageSize=5&keyword=BC371147882188902400', 'GET', None, tok)
krows = ((kd.get('data') or {}).get('rows') or [])
print('  total=', (kd.get('data') or {}).get('total'), 'rows=', [r.get('contractNo') for r in krows])

print('\n按 contractStatus=DRAFT 过滤：')
st, dd = call('/api/v1/contracts?pageNum=1&pageSize=5&contractStatus=DRAFT', 'GET', None, tok)
drows = ((dd.get('data') or {}).get('rows') or [])
print('  total=', (dd.get('data') or {}).get('total'), 'rows=', [r.get('contractNo') for r in drows])
