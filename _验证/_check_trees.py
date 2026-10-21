# -*- coding: utf-8 -*-
"""检查所有树形接口返回结构 + 前端 el-tree 使用点"""
import io
import json
import os
import re
import urllib.request

BASE = 'http://192.168.31.11:8080'
FE = r'D:\Work\业务平台开发\frontend\src'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']

req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except Exception as e:
        return {'code': type(e).__name__}


print('=' * 72)
print(' ① 树形接口实测')
print('=' * 72)
for name, path in (('组织结构树', '/api/v1/orgs/tree'),
                   ('组织子节点', '/api/v1/orgs/children'),
                   ('空间树', '/api/v1/spaces/tree?orgId=%s' % ORG),
                   ('空间子树', '/api/v1/spaces/%s/subtree' % ORG)):
    r = get(path)
    d = r.get('data')
    kind = type(d).__name__
    n = len(d) if isinstance(d, list) else (len(d.get('rows') or []) if isinstance(d, dict) else 0)
    print('\n■ %-10s %s  %s  n=%s' % (name, path.replace('/api/v1', ''), kind, n))
    if isinstance(d, list) and d:
        first = d[0]
        print('   键：%s' % sorted(first.keys()))
        has_child = 'children' in first
        print('   含 children：%s%s' % (has_child,
              ('（%d 个）' % len(first['children'])) if has_child and isinstance(first['children'], list) else ''))
        print('   首节点：%s' % json.dumps({k: first[k] for k in list(first)[:6]},
                                        ensure_ascii=False)[:220])

print('\n' + '=' * 72)
print(' ② 前端 el-tree 使用点')
print('=' * 72)
for root, _, files in os.walk(FE):
    for f in sorted(files):
        if not f.endswith('.vue'):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        if 'el-tree' not in s:
            continue
        print('\n■ %s' % f)
        for m in re.finditer(r'<el-tree[^>]*>', s):
            print('   ' + re.sub(r'\s+', ' ', m.group(0))[:200])
        for m in re.finditer(r':props="([^"]+)"', s):
            print('   props: %s' % m.group(1))
        for m in re.finditer(r"(label|children):\s*'([^']+)'", s):
            print('   %s → %s' % (m.group(1), m.group(2)))
