# -*- coding: utf-8 -*-
"""核对 /orgs/children 与 /spaces/tree 的真实返回结构"""
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
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode())


orgs = get('/api/v1/orgs/children')
print('■ /orgs/children  code=%s  data 类型=%s 长度=%s'
      % (orgs.get('code'), type(orgs.get('data')).__name__,
         len(orgs.get('data') or [])))
demo = [o for o in (orgs.get('data') or []) if '演示' in (o.get('orgName') or '')]
print('  演示组织：%s' % ([{'id': o['id'], 'name': o['orgName']} for o in demo] or '未找到'))

if demo:
    t = get('/api/v1/spaces/tree?orgId=%s' % demo[0]['id'])
    tree = t.get('data') or []
    def count(ns): return sum(1 + count(x.get('children') or []) for x in ns)
    print('\n■ /spaces/tree  code=%s  根=%d  总节点=%d' % (t.get('code'), len(tree), count(tree)))
    for b in tree[:2]:
        print('   %s [%s] 子 %d' % (b.get('spaceName'), b.get('spaceTypeLabel'),
                                   len(b.get('children') or [])))
