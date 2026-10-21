# -*- coding: utf-8 -*-
"""验证组织树的节点筛选：直接下级 / 含下级"""
import json
import urllib.request

BASE = 'http://192.168.31.11:8080'
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
            return json.loads(x.read().decode()).get('data')
    except Exception as e:
        return {'err': str(e)}


roots = get('/api/v1/orgs/children') or []
print('根组织 %d 个' % len(roots))

# 找一个有子节点的根
target = None
for n in roots:
    kids = get('/api/v1/orgs/children?parentId=%s' % n['id']) or []
    if kids:
        target = (n, kids)
        break

if not target:
    print('未找到有子节点的组织')
else:
    n, kids = target
    print('\n选中：%s（%s）' % (n['orgName'], n['id']))
    print('  直接下级 %d 个：%s' % (len(kids), [k['orgName'] for k in kids]))

    r = get('/api/v1/orgs?pageNum=1&pageSize=20&parentId=%s' % n['id'])
    print('\n■ 默认（仅下级）：total=%s' % r.get('total'))
    for x in (r.get('rows') or [])[:6]:
        print('    %-18s parent=%s' % (x['orgName'], x.get('parentIdName') or x.get('parentId')))

    r2 = get('/api/v1/orgs?pageNum=1&pageSize=20&parentId=%s&includeSubtree=true' % n['id'])
    print('\n■ 含下级：total=%s' % r2.get('total'))
    for x in (r2.get('rows') or [])[:10]:
        print('    %-18s L%s' % (x['orgName'], x.get('orgLevel')))

    r3 = get('/api/v1/orgs?pageNum=1&pageSize=5')
    print('\n■ 无筛选（全部）：total=%s' % r3.get('total'))
