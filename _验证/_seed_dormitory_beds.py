# -*- coding: utf-8 -*-
"""宿舍床位样本：在一期示范小区造一个宿舍房间 + 4 个床位（BED）房源。

验证多业态「宿舍」场景：房源挂在 BED 节点、按床位出租（BED_MONTH）。
"""
import json
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
ORG = '一期示范小区'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'message': str(e)}


def rows(resp):
    data = (resp[1] or {}).get('data')
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


def ok(resp):
    return (resp[1] or {}).get('code') == 'BP00000'


def main():
    tok = (call('/auth/login', 'POST',
                {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'})[1]
           ['data']['token'])
    org = next((x for x in rows(call('/orgs?pageNum=1&pageSize=100', token=tok))
                if x['orgName'] == ORG), None)
    if not org:
        print('未找到 %s' % ORG)
        return 1
    oid = org['id']

    tree = call('/spaces/tree?orgId=%s' % oid, token=tok)[1]['data']
    flat = []

    def walk(nodes):
        for n in nodes or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))

    floor = next((x for x in flat if x.get('spaceType') == 'FLOOR'), None)
    if not floor:
        print('未找到楼层节点')
        return 1

    # 宿舍房间
    room = next((x for x in flat if x.get('spaceCode') == 'DORM-201'), None)
    if not room:
        st, r = call('/spaces', 'POST',
                     {'orgId': oid, 'spaceCode': 'DORM-201', 'spaceName': '宿舍-201',
                      'spaceType': 'ROOM', 'parentId': floor['id'],
                      'area': 28, 'sortNo': 20}, tok)
        room = (r or {}).get('data')
        if not room:
            print('宿舍房间创建失败：%s' % (r or {}).get('message'))
            return 1
        print('宿舍房间已建：宿舍-201')

    # 4 个床位 + 床位房源
    created = 0
    for i, tag in enumerate(['A', 'B', 'C', 'D'], start=1):
        code = 'DORM-201-%s' % tag
        bed = next((x for x in flat if x.get('spaceCode') == code), None)
        if not bed:
            st, r = call('/spaces', 'POST',
                         {'orgId': oid, 'spaceCode': code,
                          'spaceName': '宿舍-201 床位%s' % tag, 'spaceType': 'BED',
                          'parentId': room['id'], 'area': 6, 'sortNo': i}, tok)
            bed = (r or {}).get('data')
            if not bed:
                print('  床位 %s 创建失败：%s' % (tag, (r or {}).get('message')))
                continue

        st, r = call('/houses', 'POST',
                     {'orgId': oid, 'spaceId': bed['id'],
                      'houseCode': 'B-%s' % code, 'houseName': '宿舍-201 床位%s' % tag,
                      'houseType': 'DORMITORY', 'useType': 'CIVIL', 'area': 6,
                      'rentStandard': 200, 'rentUnit': 'BED_MONTH',
                      'maxCapacity': 1, 'houseStatus': 'VACANT'}, tok)
        if ok((st, r)):
            created += 1
        else:
            print('  床位房源 %s 失败：%s' % (tag, (r or {}).get('message')))

    print('床位房源：新增 %d 个' % created)

    st, r = call('/houses?pageNum=1&pageSize=20&houseType=DORMITORY&orgId=%s' % oid, token=tok)
    items = ((r or {}).get('data') or {}).get('rows') or []
    print('宿舍类房源 %d 个：' % len(items))
    for h in items[:6]:
        print('   %-18s 空间=%-14s 类型=%s 租金单位=%s'
              % (h.get('houseName'), h.get('spaceName') or '-',
                 h.get('spaceType') or '-', h.get('rentUnit')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
