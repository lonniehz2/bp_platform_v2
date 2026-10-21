# -*- coding: utf-8 -*-
"""单次调用通行上报并立即读取日志尾部，定位异常"""
import json
import subprocess
import sys
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
H = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}


def call(m, p, b=None, tok=None):
    h = dict(H)
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, x.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


st, raw = call('POST', '/api/v1/auth/login',
               {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})
tok = json.loads(raw)['data']['token']
print('登录 OK')

st, raw = call('POST', '/api/v1/access-records', {
    'eventId': 'DIAG-%d' % __import__('time').time(),
    'lockId': 'LOCK-DIAG', 'houseId': 999001, 'orgId': 1,
    'openType': '1001', 'personId': 888001,
    'openTime': '2026-10-18T09:00:00', 'source': 'CALLBACK'}, tok)
print('上报 HTTP %s' % st)
print('响应: %s' % raw[:400])

print()
print('=== 日志尾部（含异常） ===')
req = ("tail -60 /var/log/bp-platform/app.log | grep -iE 'ERROR|Exception|Caused|###' "
       "| tail -12")
p = subprocess.run([sys.executable, 'vm.py', req], capture_output=True, text=True,
                   encoding='utf-8', errors='replace', cwd=r'D:\Work\业务平台开发\_验证')
print(p.stdout[-2500:] if p.stdout else p.stderr[-1500:])
