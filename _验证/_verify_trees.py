# -*- coding: utf-8 -*-
"""验证两类树的层级深度与渲染数据"""
import json
import urllib.request

BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode()).get('data')


def depth(nodes, d=1):
    if not nodes:
        return d - 1
    best = d
    for n in nodes:
        ch = n.get('children') or []
        if ch:
            best = max(best, depth(ch, d + 1))
    return best


def count(nodes):
    return sum(1 + count(n.get('children') or []) for n in (nodes or []))


# 模拟前端递归：从 /orgs/children 逐层展开
def build(pid=None, d=1, seen=None):
    seen = seen or set()
    out = []
    for n in get('/api/v1/orgs/children' + ('?parentId=%s' % pid if pid else '')) or []:
        if n['id'] in seen:
            continue
        seen.add(n['id'])
        node = dict(n)
        if d < 6:
            kids = build(n['id'], d + 1, seen)
            if kids:
                node['children'] = kids
        out.append(node)
    return out


print('■ 组织结构树（前端递归模拟）')
t = build()
print('   根节点 %d 个，总节点 %d 个，最大深度 %d 层' % (len(t), count(t), depth(t)))
for n in t:
    if n.get('children'):
        print('   ├ %s (%d 子)' % (n['orgName'], len(n['children'])))
        for c in n['children']:
            if c.get('children'):
                print('   │  └ %s (%d 子)' % (c['orgName'], len(c['children'])))

print('\n■ 空间树（后端一次返回）')
sp = get('/api/v1/spaces/tree?orgId=%s' % D['orgId'])
print('   根节点 %d 个，总节点 %d 个，最大深度 %d 层'
      % (len(sp or []), count(sp), depth(sp)))


def walk(nodes, d=1, tag=''):
    for n in nodes or []:
        print('   %s%s [%s]' % ('  ' * (d - 1), n.get('spaceName'),
                                n.get('spaceTypeLabel') or n.get('spaceType')))
        walk(n.get('children'), d + 1)


walk(sp)
