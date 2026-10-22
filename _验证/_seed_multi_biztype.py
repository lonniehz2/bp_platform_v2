# -*- coding: utf-8 -*-
"""多业态样本：在一期示范小区下补充 公寓 / 宿舍 / 酒店民宿 三类房源，验证业态隔离。"""
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
        print('未找到楼层节点，先运行 _seed_phase1.py')
        return 1

    PLAN = [
        ('D-R1', '公寓-1601', 'APARTMENT', 45, 55),
        ('D-R2', '公寓-1602', 'APARTMENT', 48, 58),
        ('D-R3', '宿舍-201', 'DORMITORY', 25, 20),
        ('D-R4', '宿舍-202', 'DORMITORY', 25, 20),
        ('D-R5', '酒店-8801', 'HOTEL', 30, 180),
    ]

    created = 0
    for code, name, htype, area, rent in PLAN:
        room = next((x for x in flat if x.get('spaceCode') == code), None)
        if not room:
            st, r = call('/spaces', 'POST',
                         {'orgId': oid, 'spaceCode': code, 'spaceName': name,
                          'spaceType': 'ROOM', 'parentId': floor['id'],
                          'area': area, 'sortNo': 9}, tok)
            room = (r or {}).get('data')
            if not room:
                print('  房间 %s 失败：%s' % (code, (r or {}).get('message')))
                continue
        st, r = call('/houses', 'POST',
                     {'orgId': oid, 'spaceId': room['id'],
                      'houseCode': 'M-' + code, 'houseName': '%s%s' % (ORG, name),
                      'houseType': htype, 'useType': 'CIVIL', 'area': area,
                      'rentStandard': rent,
                      'rentUnit': 'HOUSE_NIGHT' if htype == 'HOTEL' else 'AREA_MONTH',
                      'houseStatus': 'VACANT'}, tok)
        if ok((st, r)):
            created += 1
        else:
            print('  房源 %s 失败：%s' % (name, (r or {}).get('message')))
    print('多业态样本：新增 %d 套' % created)

    for t, label in [('PUBLIC_RENTAL', '公租房'), ('APARTMENT', '公寓'),
                     ('DORMITORY', '宿舍'), ('HOTEL', '酒店/民宿')]:
        st, r = call('/houses?pageNum=1&pageSize=1&houseType=%s&orgId=%s' % (t, oid), token=tok)
        total = ((r or {}).get('data') or {}).get('total')
        print('  %-8s %s 套' % (label, total))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
