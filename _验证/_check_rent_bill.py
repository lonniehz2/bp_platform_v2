# -*- coding: utf-8 -*-
import json
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


login = call('/auth/login', 'POST',
             {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})
tok = login['data']['token']
body = {
    'feeItemId': 374371142242275328,
    'periodStart': '2026-11-01',
    'periodEnd': '2026-11-30',
    'billPeriod': '2026-11',
    'contractIds': [374466995221041152],
    'dryRun': True
}
r = call('/fin/bills/generate', 'POST', body, tok)
d = r['data']
print('合计', d['totalAmount'], '生成', d['generated'])
for it in d['items']:
    print('合同', it['contractNo'], '金额', it['amount'], '说明', it['explain'])
