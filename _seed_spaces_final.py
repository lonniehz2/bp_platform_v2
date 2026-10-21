# -*- coding: utf-8 -*-
"""清理无法使用的 AREA 节点（该层级不允许子节点），并输出最终结构"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D.get('demoOrgId')


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
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

# 删除空的东片区（AREA 不能挂子节点，留着会造成误解）
st, r = call('GET', '/api/v1/spaces/tree?orgId=%s' % ORG, None, TOK)
tree = r.get('data') or []
for n in tree:
    if n.get('spaceType') == 'AREA':
        st2, r2 = call('DELETE', '/api/v1/spaces/%s' % n['id'], None, TOK)
        print('删除片区「%s」：%s %s' % (n.get('spaceName'), r2.get('code'),
                                      str(r2.get('message'))[:40]))

# 最终结构
st, r = call('GET', '/api/v1/spaces/tree?orgId=%s' % ORG, None, TOK)
tree = r.get('data') or []


def count(nodes):
    return sum(1 + count(x.get('children') or []) for x in nodes)


def depth(nodes, d=1):
    if not nodes:
        return d - 1
    return max(depth(x.get('children') or [], d + 1) for x in nodes)


print('\n最终：根 %d ｜ 总节点 %d ｜ 深度 %d 层'
      % (len(tree), count(tree), depth(tree)))
for b in tree:
    kids = b.get('children') or []
    unit_n = sum(count(u.get('children') or []) for u in kids)
    print('  ├ %s [%s]：%d 单元 / 共 %d 节点'
          % (b.get('spaceName'), b.get('spaceTypeLabel'),
             len(kids), unit_n))
