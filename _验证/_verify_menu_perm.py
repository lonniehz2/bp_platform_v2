# -*- coding: utf-8 -*-
"""验证 /auth/me 返回的权限码是否覆盖路由声明的 perm（否则菜单会消失）"""
import io
import json
import re
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

need = {}
for m in re.finditer(r"path:\s*'/([a-z\-]+)'[\s\S]{0,400}?meta:\s*\{([^}]*)\}", s):
    pm = re.search(r"perm:\s*'([^']+)'", m.group(2))
    if pm:
        need[m.group(1)] = pm.group(1)


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


for acct, pwd in (('admin', 'admin123'), ('viewer', 'view123')):
    tok = call('POST', '/api/v1/auth/login',
               {'tenantId': '350600', 'username': acct, 'password': pwd}
               ).get('data', {}).get('token')
    me = call('GET', '/api/v1/auth/me', None, tok).get('data') or {}
    perms = set(me.get('permissions') or me.get('permCodes') or [])
    print('\n%s 权限 %d 个' % (acct, len(perms)))
    if perms:
        print('  样例：%s' % ', '.join(sorted(perms)[:8]))
    miss = {k: v for k, v in need.items() if v not in perms}
    print('  路由声明 perm 的页面 %d 个，缺权限导致隐藏 %d 个：%s'
          % (len(need), len(miss),
             ', '.join('/' + k for k in miss) if miss else '无'))
