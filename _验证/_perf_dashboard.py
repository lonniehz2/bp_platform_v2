# -*- coding: utf-8 -*-
"""测量驾驶舱关键接口耗时（数据量重建后）。"""
import json
import time
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'


def post(path, body):
    req = urllib.request.Request(B + path, data=json.dumps(body).encode(),
                                 method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


def timed(path, tok):
    t0 = time.time()
    q = urllib.request.Request(B + path, headers={'Authorization': 'Bearer ' + tok,
                                                  'X-Tenant-Id': '350600'})
    with urllib.request.urlopen(q, timeout=120) as x:
        x.read()
    return (time.time() - t0) * 1000


login = post('/auth/login', {'tenantCode': '350600', 'username': 'admin',
                             'password': 'admin123'})
tok = login['data']['token']

for ep in ['/fin/bills/trend?months=6',
           '/fin/meter-readings/analytics?months=6',
           '/fin/deposits?pageNum=1&pageSize=1',
           '/workorders?pageNum=1&pageSize=1',
           '/metrics/overview']:
    try:
        print('%-46s %6.0f ms' % (ep, timed(ep, tok)))
    except Exception as ex:
        print('%-46s 失败: %s' % (ep, str(ex)[:50]))
