# -*- coding: utf-8 -*-
"""补造车库与车位（顶级节点）+ 一个片区"""
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


def mk(code, name, stype, parent=None, sort=1, area=None):
    body = {'orgId': ORG, 'spaceCode': code, 'spaceName': name,
            'spaceType': stype, 'sortNo': sort}
    if parent:
        body['parentId'] = parent
    if area:
        body['area'] = area
    st, r = call('POST', '/api/v1/spaces', body, TOK)
    sid = (r.get('data') or {}).get('id')
    print('   %s %-14s %-10s → %s %s'
          % ('✓' if r.get('code') == 'BP00000' else '✗', name, stype, sid or '-',
             '' if sid else str(r.get('message'))[:44]))
    return sid


print('— 车库与车位（顶级车库）—')
garage = mk('DEMO-GARAGE', '地下车库', 'GARAGE', None, sort=9)
if garage:
    for i in range(1, 9):
        mk('DEMO-GARAGE-P%02d' % i, '车位%02d' % i, 'PARKING', garage, sort=i)

print('\n— 片区（AREA 顶级）—')
area = mk('DEMO-AREA-E', '东片区', 'AREA', None, sort=1)
if area:
    b = mk('DEMO-AREA-E-B1', '东片区C栋', 'BUILDING', area, sort=1)
    if b:
        mk('DEMO-AREA-E-B1-U1', 'C栋1单元', 'UNIT', b)

print('\n— 树形校验 —')
st, r = call('GET', '/api/v1/spaces/tree?orgId=%s' % ORG, None, TOK)
tree = r.get('data') or []


def walk(nodes, d=1):
    n = 0
    for x in nodes:
        n += 1
        print('   ' + '  ' * (d - 1) + '%s [%s]'
              % (x.get('spaceName'), x.get('spaceTypeLabel') or x.get('spaceType')))
        n += walk(x.get('children') or [], d + 1)
    return n


total = walk(tree)


def depth(nodes, d=1):
    if not nodes:
        return d - 1
    return max(depth(x.get('children') or [], d + 1) for x in nodes)


print('\n根节点 %d 个｜总节点 %d 个｜最大深度 %d 层'
      % (len(tree), total, depth(tree)))
