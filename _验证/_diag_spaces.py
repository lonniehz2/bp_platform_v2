# -*- coding: utf-8 -*-
"""定位 /spaces/tree 可用参数 + 校验字典已恢复"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
ORG = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json',
                     encoding='utf-8'))['orgId']
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

for p in ('/api/v1/spaces/tree',
          '/api/v1/spaces/tree?orgId=%s' % ORG,
          '/api/v1/spaces/children'):
    st, r = call('GET', p)
    d = r.get('data')
    n = len(d) if isinstance(d, list) else (d.get('total') if isinstance(d, dict) else 0)
    print('  %-42s HTTP%s %s n=%s %s'
          % (p.replace('/api/v1', ''), st, r.get('code'), n,
             str(r.get('message'))[:46]))

st, r = call('GET', '/api/v1/sys/dicts/HOUSE_TYPE')
print('\n  字典 HOUSE_TYPE：%s 项 %s' % (len(r.get('data') or []), r.get('code')))
st, r = call('GET', '/api/v1/sys/dicts/SECURITY_TYPE')
print('  字典 SECURITY_TYPE：%s 项' % len(r.get('data') or []))
