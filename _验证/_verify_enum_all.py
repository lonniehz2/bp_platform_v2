# -*- coding: utf-8 -*-
"""验证：申请列表返回 personName + 枚举前端映射覆盖情况"""
import io
import json
import os
import re
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
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

r = call('GET', '/api/v1/applications?pageNum=1&pageSize=3')
rows = (r.get('data') or {}).get('rows') or []
print('■ 申请列表 %s，%d 行' % (r.get('code'), len(rows)))
for x in rows:
    print('   %s | 申请人=%s | 保障类型=%s | 环节=%s | 状态=%s'
          % (x.get('applicationNo'), x.get('personName') or ('ID:' + str(x.get('personId'))),
             x.get('securityType'), x.get('currentNode'), x.get('applicationStatus')))

# 前端枚举覆盖统计
E = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'
es = io.open(E, encoding='utf-8').read()
keys = re.findall(r"^  '?([A-Z][A-Z_0-9]+)'?:\s*'", es, re.M)
print('\n■ enums.js 枚举条目：%d 个' % len(keys))

V = r'D:\Work\业务平台开发\frontend\src\views'
calls = 0
files = 0
for f in os.listdir(V):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    n = len(re.findall(r'enumLabel\(', s))
    if n:
        calls += n
        files += 1
print('■ 已接入 enumLabel：%d 处 / %d 个页面' % (calls, files))
