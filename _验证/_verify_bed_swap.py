# -*- coding: utf-8 -*-
"""床位调换端到端验证：签床 → 调到另一张床 → 校验状态与占用；再调回已占床应被拒。"""
import json
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

API = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def d(resp):
    return (resp[1] or {}).get('data')


def ok(resp):
    return (resp[1] or {}).get('code') == 'BP00000'


def rows(resp):
    data = d(resp)
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


tok = d(call('/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin',
              'password': 'admin123'}))['token']

org = next(o for o in rows(call('/orgs?pageNum=1&pageSize=100', token=tok))
           if o['orgName'] == '一期示范小区')
oid = org['id']

tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
flat = []


def walk(ns):
    for n in ns or []:
        flat.append(n)
        walk(n.get('children'))


walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
room = next(x for x in flat if x.get('spaceType') == 'ROOM')

# 确保该房间有 2 张床位
call('/houses/beds/batch-create', 'POST',
     {'roomSpaceId': room['id'], 'count': 2, 'rentStandard': 300, 'areaPerBed': 8}, tok)
beds = rows(call('/houses/beds?roomSpaceId=%s' % room['id'], token=tok))
print('床位:', [(b['bedCode'], b['occupied']) for b in beds])

free = [b for b in beds if not b['occupied']]
if len(free) < 2:
    print('可用空床不足 2 张，先清理测试床位')
    raise SystemExit(1)

b1, b2 = free[0], free[1]

# 建人
W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
base = ('33010619900101%03d' % (int(time.time()) % 1000))[:17]
idc = base + '10X98765432'[sum(int(base[i]) * W[i] for i in range(17)) % 11]
person = d(call('/persons', 'POST',
                {'personName': '床位调换测试', 'idCard': idc,
                 'phone': '137%08d' % (int(time.time()) % 100000000),
                 'orgId': oid, 'householdType': 'URBAN'}, tok))
if not person:
    print('建人失败')
    raise SystemExit(1)

st, r = call('/contracts/quick-sign', 'POST',
             {'personId': person['id'], 'houseId': b1['houseId'],
              'leaseStart': str(date.today()),
              'leaseEnd': str(date.today() + timedelta(days=180)),
              'monthlyRent': 300, 'depositAmount': 300,
              'securityType': 'PUBLIC', 'remark': '床位调换测试'}, tok)
c = d((st, r)) or {}
cid = c.get('id')
print('签床合同:', st, (r or {}).get('code'), c.get('contractNo'))
if cid:
    for path, body in (('/submit-sign', {}), ('/start-signing', {}),
                       ('/sign', {'signType': 'ELECTRONIC'})):
        s2, r2 = call('/contracts/%s%s' % (cid, path), 'POST', body, tok)
        if not ok((s2, r2)):
            print('  签约步骤失败', path, (r2 or {}).get('message'))
    st3, r3 = call('/contracts/%s' % cid, token=tok)
    eff = d((st3, r3)) or {}
    print('合同状态:', eff.get('contractStatus'), '房源:', eff.get('houseId'))

    st4, r4 = call('/contracts/%s/swap-bed' % cid, 'POST',
                   {'targetHouseId': b2['houseId'], 'reason': '测试调换'}, tok)
    print('调换到', b2['bedCode'], ':', st4, (r4 or {}).get('code'),
          (r4 or {}).get('message', ''))
    after = rows(call('/houses/beds?roomSpaceId=%s' % room['id'], token=tok))
    for b in after:
        if b['bedCode'] in (b1['bedCode'], b2['bedCode']):
            print('  %s occupied=%s occupant=%s' % (b['bedCode'], b['occupied'],
                                                    b.get('occupant')))

    # 再调到已被自己占用的床之外的另一张已占床（构造：调到 b1，此时 b1 应已释放）
    st5, r5 = call('/contracts/%s/swap-bed' % cid, 'POST',
                   {'targetHouseId': b1['houseId'], 'reason': '调回原床'}, tok)
    print('调回原床:', st5, (r5 or {}).get('code'))

    # 另一人占用 b2 后，合同再调向 b2 应被拒绝
    base2 = ('33010619900202%03d' % ((int(time.time()) + 7) % 1000))[:17]
    idc2 = base2 + '10X98765432'[sum(int(base2[i]) * W[i] for i in range(17)) % 11]
    p2 = d(call('/persons', 'POST',
                {'personName': '占床测试对象', 'idCard': idc2,
                 'phone': '136%08d' % ((int(time.time()) + 3) % 100000000),
                 'orgId': oid, 'householdType': 'URBAN'}, tok))
    stc, rc = call('/contracts/quick-sign', 'POST',
                   {'personId': p2['id'], 'houseId': b2['houseId'],
                    'leaseStart': str(date.today()),
                    'leaseEnd': str(date.today() + timedelta(days=180)),
                    'monthlyRent': 300, 'depositAmount': 300,
                    'securityType': 'PUBLIC', 'remark': '占床测试'}, tok)
    c2 = (d((stc, rc)) or {}).get('id')
    for path, body in (('/submit-sign', {}), ('/start-signing', {}),
                       ('/sign', {'signType': 'ELECTRONIC'})):
        call('/contracts/%s%s' % (c2, path), 'POST', body, tok)
    st6, r6 = call('/contracts/%s/swap-bed' % cid, 'POST',
                   {'targetHouseId': b2['houseId'], 'reason': '占用冲突测试'}, tok)
    print('调向他人在租床（应拒绝）:', st6, (r6 or {}).get('code'),
          (r6 or {}).get('message', '')[:40])
