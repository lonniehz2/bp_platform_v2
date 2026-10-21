# -*- coding: utf-8 -*-
"""打印登录接口的完整响应，确认失败原因"""
import json
import urllib.error
import urllib.request

B = 'http://192.168.31.11:8080/api/v1/auth/login'

for body, tag in (
        ({'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}, 'admin'),
        ({'tenantId': '350600', 'username': 'acceptor', 'password': 'acc123'}, 'acceptor'),
        ({'tenantId': '350600', 'username': 'viewer', 'password': 'view123'}, 'viewer')):
    d = json.dumps(body).encode()
    r = urllib.request.Request(B, data=d, method='POST',
                              headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=15) as x:
            print('%-10s HTTP %s  %s' % (tag, x.status, x.read().decode()[:200]))
    except urllib.error.HTTPError as e:
        print('%-10s HTTP %s  %s' % (tag, e.code, e.read().decode()[:200]))
    except Exception as e:
        print('%-10s %s' % (tag, type(e).__name__))
