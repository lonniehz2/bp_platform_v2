# -*- coding: utf-8 -*-
"""验证新增 8 个页面的接口（含动作接口可用性）"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
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

CHECKS = [
    ('申诉列表', 'GET', '/api/v1/appeals?pageNum=1&pageSize=5'),
    ('申诉超时标记', 'POST', '/api/v1/appeals/mark-timeout'),
    ('信用列表', 'GET', '/api/v1/credits?pageNum=1&pageSize=5'),
    ('信用扫描到期', 'POST', '/api/v1/credits/scan-expired'),
    ('换房列表', 'GET', '/api/v1/exchanges?pageNum=1&pageSize=5'),
    ('投诉列表', 'GET', '/api/v1/complaints?pageNum=1&pageSize=5'),
    ('告警列表', 'GET', '/api/v1/alerts?pageNum=1&pageSize=5'),
    ('告警统计', 'GET', '/api/v1/alerts/stats'),
    ('钥匙包列表', 'GET', '/api/v1/keyring?pageNum=1&pageSize=5'),
    ('工单列表', 'GET', '/api/v1/workorders?pageNum=1&pageSize=5'),
    ('人员列表', 'GET', '/api/v1/persons?pageNum=1&pageSize=5'),
    ('房源列表', 'GET', '/api/v1/houses?pageNum=1&pageSize=5'),
    ('设备列表', 'GET', '/api/v1/devices?pageNum=1&pageSize=5'),
]

print('=' * 68)
print(' 新增页面接口验证')
print('=' * 68)
bad = []
for name, m, p in CHECKS:
    st, r = call(m, p)
    code = r.get('code')
    ok = st == 200 and code == 'BP00000'
    d = r.get('data')
    n = ''
    if isinstance(d, dict):
        n = str(d.get('total') or len(d.get('rows') or []) or '')
    elif isinstance(d, list):
        n = str(len(d))
    print('  %s %-14s %-6s %s %s'
          % ('✓' if ok else '✗', name, m, code, n))
    if not ok:
        bad.append((name, code, str(r.get('message'))[:60]))

print()
if bad:
    print(' 失败 %d 项：' % len(bad))
    for x in bad:
        print('   %s %s %s' % x)
else:
    print(' ✔ 全部通过（%d 项）' % len(CHECKS))
