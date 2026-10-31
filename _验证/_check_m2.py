# -*- coding: utf-8 -*-
import json
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'
POINT = 1793419865712010


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


tok = call('/auth/login', 'POST',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
r = call('/fin/utility-allocations/preview', 'POST',
         {'period': '2026-10', 'meterPointId': POINT}, tok)['data']
print('整表', r['totalUsage'], r['totalAmount'], '运营方', r['operatorBearAmount'])
for s in r['shares']:
    print(s['contractNo'], s['lesseeName'], s['occupyDays'], s['personDays'],
          s['shareRatio'], s['shareAmount'])
print('sum shares', sum(float(s['shareAmount']) for s in r['shares']))
