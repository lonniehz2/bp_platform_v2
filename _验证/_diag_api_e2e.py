# -*- coding: utf-8 -*-
"""直连接口复现：新增人员 / 新建合同的真实响应"""
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
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:400]


st, d = call('/api/v1/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = (d.get('data') or {}).get('accessToken') or (d.get('data') or {}).get('token')
print('login', st, 'token?', bool(tok))

print('\n--- 新增人员（只填姓名+手机号）---')
print(call('/api/v1/persons', 'POST',
           {'personName': 'DIAG人员A', 'phone': '13900001111'}, tok))

print('\n--- 新增人员（带合法身份证号）---')
print(call('/api/v1/persons', 'POST',
           {'personName': 'DIAG人员B', 'phone': '13900002222',
            'idCard': '110101199003077758'}, tok))

print('\n--- 新建合同（含起止日期）---')
hs, hd = call('/api/v1/houses?pageNum=1&pageSize=3&houseStatus=VACANT', 'GET', None, tok)
rows = (hd.get('data') or {}).get('rows') or []
print('房源样例：', [(r.get('id'), r.get('houseName')) for r in rows])
ps, pd = call('/api/v1/persons?pageNum=1&pageSize=3', 'GET', None, tok)
prow = ((pd.get('data') or {}).get('rows') or [{}])[0]
if rows:
    h = rows[0]
    print(call('/api/v1/contracts', 'POST', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': 1,
        'lesseePersonId': prow.get('id'), 'lesseeName': prow.get('personName'),
        'lesseePhone': '13900001111',
        'houseId': h.get('id'), 'houseAddress': h.get('houseName'),
        'leaseStart': '2026-11-01', 'leaseEnd': '2027-10-31',
        'monthlyRent': 1000, 'depositAmount': 1000,
        'payCycle': 'MONTH', 'payDay': 5, 'rentUnit': 'MONTH',
    }, tok))
