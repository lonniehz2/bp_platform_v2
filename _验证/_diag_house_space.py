# -*- coding: utf-8 -*-
"""确认房源是否带 spaceId，并用完整字段验证合同创建"""
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
            return e.code, raw[:300]


st, d = call('/api/v1/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = (d.get('data') or {}).get('accessToken')
print('login keys:', list(((d.get('data') or {}).keys())))
tok = tok or (d.get('data') or {}).get('token')

st, hd = call('/api/v1/houses?pageNum=1&pageSize=2&houseStatus=VACANT', 'GET', None, tok)
h = ((hd.get('data') or {}).get('rows') or [{}])[0]
print('房源字段:', json.dumps(h, ensure_ascii=False, indent=1)[:900])

st, pd = call('/api/v1/persons?pageNum=1&pageSize=1', 'GET', None, tok)
p = ((pd.get('data') or {}).get('rows') or [{}])[0]

payload = {
    'contractType': 'PUBLIC_RENTAL', 'orgId': 1, 'lessorOrgId': 1,
    'lesseePersonId': p.get('id'), 'lesseeName': p.get('personName'),
    'lesseePhone': '13900001111',
    'houseId': h.get('id'), 'spaceId': h.get('spaceId'),
    'houseAddress': h.get('houseName'),
    'leaseStart': '2026-11-01', 'leaseEnd': '2027-10-31',
    'rentPrice': 20, 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': 1000,
    'depositAmount': 1000, 'payCycle': 'MONTH', 'payDay': 5,
}
print('\n合同请求 spaceId =', h.get('spaceId'))
st, cd = call('/api/v1/contracts', 'POST', payload, tok)
print('合同创建:', st, json.dumps(cd, ensure_ascii=False)[:500])
