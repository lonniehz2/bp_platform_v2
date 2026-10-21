# -*- coding: utf-8 -*-
"""为什么新建人员不出现在列表首页"""
import json
import urllib.parse
import urllib.request

BASE = 'http://192.168.31.11:8080'


def call(path, token=None, method='GET', body=None):
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
        return e.code, e.read().decode()[:400]


st, d = call('/api/v1/auth/login', method='POST',
             body={'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = (d.get('data') or {}).get('token')

st, cd = call('/api/v1/persons', tok, 'POST', {'personName': 'DIAG排序验证', 'phone': '13700009999'})
new_id = (cd.get('data') or {}).get('id')
print('新建 id =', new_id, 'code=', cd.get('code'))

st, kd = call('/api/v1/persons?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote('DIAG排序验证'), tok)
print('按名字查：total=', (kd.get('data') or {}).get('total'),
      [(r.get('personName'), r.get('id')) for r in ((kd.get('data') or {}).get('rows') or [])])

st, gd = call('/api/v1/persons/' + str(new_id), tok)
print('按 id 查：', st, (gd.get('data') or {}).get('personName') if isinstance(gd, dict) else gd)

st, ld = call('/api/v1/persons?pageNum=1&pageSize=3', tok)
print('首页：', [(r.get('personName'), r.get('id'), r.get('createTime')) for r in ((ld.get('data') or {}).get('rows') or [])])
