# -*- coding: utf-8 -*-
"""核对大屏/指标接口真实返回：title 是否中文、widgets 是否有值"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__}


tok = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

d = call('GET', '/api/v1/rpt/screens/OVERVIEW/data', None, tok).get('data') or {}
print('screenName = %s' % d.get('screenName', '(缺 screenName)'))
print('refreshSeconds = %s' % d.get('refreshSeconds'))
ws = d.get('widgets') or []
print('widgets = %d 个\n' % len(ws))
print('  %-22s %-10s %-8s %s' % ('code', 'title', 'chart', 'value'))
for w in ws:
    print('  %-22s %-10s %-8s %s'
          % (w.get('code'), w.get('title'), w.get('chart'), w.get('value')))

m = call('GET', '/api/v1/rpt/metrics/current', None, tok).get('data') or {}
print('\nmetrics 键（%d）：' % len(m))
for k, v in m.items():
    print('  %-24s %s' % (k, v))
