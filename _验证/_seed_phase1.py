# -*- coding: utf-8 -*-
"""一期示范数据（完整链路）。

链路：组织/空间/房源 → 人员/保障档案 → 申请 → 审核通过（自动入轮候）
      → 批次(含房源) → 发布 → 报名 → 摇号 → 公示(关联批次)
      → 合同(快捷签约) → 账单/收款/押金

用法：
  python _seed_phase1.py          # 造数（幂等：已存在则复用）
  python _seed_phase1.py --dry    # 打印计划
"""
import json
import sys
import urllib.parse
import urllib.error
import urllib.request
from datetime import date, timedelta

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
TAG = '一期示范'
DRY = '--dry' in sys.argv


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


def d(resp):
    return (resp[1] or {}).get('data')


def msg(resp):
    return '%s %s' % ((resp[1] or {}).get('code'), (resp[1] or {}).get('message') or '')



W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
C = '10X98765432'


def make_id(prefix17):
    """生成校验位正确的 18 位身份证号"""
    total = sum(int(prefix17[i]) * W[i] for i in range(17))
    return prefix17 + C[total % 11]


def login():
    return d(call('/auth/login', 'POST',
                  {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'}))['token']


PERSONS = [
    ('张一期', make_id('33010619900101001'), '13900000001', 'URBAN'),
    ('李二期', make_id('33010619920202002'), '13900000002', 'URBAN'),
    ('王三期', make_id('33010619930303003'), '13900000003', 'RURAL'),
    ('赵四期', make_id('33010619940404004'), '13900000004', 'URBAN'),
    ('钱待审', make_id('33010619950505005'), '13900000005', 'URBAN'),
    ('孙退租', make_id('33010619960606006'), '13900000006', 'RURAL'),
]


def main():
    tok = login()
    print('登录成功')

    if DRY:
        print('计划：组织/空间/6 套房源/6 名人员/5 份申请/1 批次/4 份合同/账单收款押金')
        return 0

    # ---------- 1) 组织 ----------
    st, r = call('/orgs?pageNum=1&pageSize=100', token=tok)
    org = next((x for x in (d((st, r)) or {}).get('rows') or []
                if x['orgName'] == TAG + '小区'), None)
    if not org:
        st, r = call('/orgs', 'POST',
                     {'orgCode': 'PHASE1', 'orgName': TAG + '小区', 'orgType': 'COMMUNITY',
                      'parentId': None, 'sortNo': 1, 'remark': '一期示范数据'}, tok)
        org = d((st, r))
    if not org:
        print('组织创建失败：', msg((st, r)))
        return 1
    org_id = org['id']
    print('组织：%s' % org['orgName'])

    # ---------- 2) 空间 ----------
    st, r = call('/spaces/tree?orgId=%s' % org_id, token=tok)
    tree = d((st, r))
    spaces = []

    def walk(nodes):
        for n in nodes or []:
            spaces.append(n)
            walk(n.get('children'))
    if isinstance(tree, list):
        walk(tree)
    elif isinstance(tree, dict):
        spaces = (tree.get('rows') or [])
    building = next((x for x in spaces if x.get('spaceCode') == 'P1-B1'), None)
    if not building:
        st, r = call('/spaces', 'POST',
                     {'orgId': org_id, 'spaceCode': 'P1-B1', 'spaceName': '1号楼',
                      'spaceType': 'BUILDING', 'sortNo': 1}, tok)
        building = d((st, r))
        if not building:
            print('楼栋创建失败：', msg((st, r)))
            return 1
    unit = next((x for x in spaces if x.get('spaceCode') == 'P1-B1-U1'), None)
    if not unit:
        st, r = call('/spaces', 'POST',
                     {'orgId': org_id, 'spaceCode': 'P1-B1-U1', 'spaceName': '1单元',
                      'spaceType': 'UNIT', 'parentId': building['id'], 'sortNo': 1}, tok)
        unit = d((st, r)) or building
    print('空间：%s / %s' % (building.get('spaceName'), unit.get('spaceName')))

    # ---------- 3) 房源 ----------
    st, r = call('/houses?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok)
    houses = (d((st, r)) or {}).get('rows') or []
    if len(houses) < 6:
        # 楼层节点（单元下只能是楼层）
        floor = next((x for x in spaces if x.get('spaceCode') == 'P1-F1'), None)
        if not floor:
            st, r = call('/spaces', 'POST',
                         {'orgId': org_id, 'spaceCode': 'P1-F1', 'spaceName': '1层',
                          'spaceType': 'FLOOR', 'parentId': unit['id'], 'sortNo': 1}, tok)
            floor = d((st, r))
            if not floor:
                print('  楼层创建失败：%s' % msg((st, r)))
        for i in range(1, 7):
            # 房间节点（房源必须挂 ROOM）
            room = next((x for x in spaces if x.get('spaceCode') == 'P1-R%d' % i), None)
            if not room:
                st, r = call('/spaces', 'POST',
                             {'orgId': org_id, 'spaceCode': 'P1-R%d' % i,
                              'spaceName': '1单元%03d室' % i, 'spaceType': 'ROOM',
                              'parentId': floor['id'], 'area': 60 + i, 'sortNo': i}, tok)
                room = d((st, r))
                if not room:
                    print('  房间 %d 失败：%s' % (i, msg((st, r))))
                    continue
            st, r = call('/houses', 'POST',
                         {'orgId': org_id, 'spaceId': room['id'],
                          'houseCode': 'P1-%03d' % i,
                          'houseName': '%s1号楼1单元%03d室' % (TAG, i),
                          'houseType': 'PUBLIC_RENTAL', 'useType': 'CIVIL',
                          'area': 60 + i, 'rentStandard': 15, 'rentUnit': 'AREA_MONTH',
                          'houseStatus': 'VACANT'}, tok)
            if (r or {}).get('code') != 'BP00000':
                print('  房源 %d 失败：%s' % (i, msg((st, r))))
        st, r = call('/houses?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok)
        houses = (d((st, r)) or {}).get('rows') or []

    print('房源：%d 套' % len(houses))
    if len(houses) < 4:
        print('房源不足，终止')
        return 1

    # ---------- 4) 人员 ----------
    st, r = call('/persons?pageNum=1&pageSize=200&keyword=%s' % urllib.parse.quote(TAG), token=tok)
    persons = (d((st, r)) or {}).get('rows') or []
    have = {p.get('realName') or p.get('personName') for p in persons}
    people = []
    for name, idcard, phone, htype in PERSONS:
        p = next((x for x in persons
                  if (x.get('realName') or x.get('personName')) == name), None)
        if not p:
            st, r = call('/persons', 'POST',
                         {'personName': name, 'idCard': idcard, 'phone': phone,
                          'orgId': org_id, 'householdType': htype,
                          'remark': '一期示范数据'}, tok)
            p = d((st, r))
            if not p:
                print('  人员 %s 失败：%s' % (name, msg((st, r))))
                continue
        people.append(p)
    print('人员：%d 名' % len(people))
    if len(people) < 4:
        print('人员不足，终止')
        return 1

    # ---------- 5) 申请 + 审核 ----------
    st, r = call('/applications?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok)
    apps = (d((st, r)) or {}).get('rows') or []
    by_person = {a.get('personId'): a for a in apps}
    created = 0
    for idx, p in enumerate(people):
        if p['id'] in by_person:
            continue
        st, r = call('/applications', 'POST',
                     {'orgId': org_id, 'personId': p['id'], 'securityType': 'PUBLIC',
                      'securityMode': 'HOUSE', 'applyChannel': 'ONLINE',
                      'familySize': 2, 'declaredIncome': 5000,
                      'remark': '一期示范数据 %d' % (idx + 1)}, tok)
        a = d((st, r))
        if a:
            by_person[p['id']] = a
            created += 1
        else:
            print('  申请失败(%s)：%s' % (p.get('realName') or p.get('personName'),
                                      msg((st, r))))
    print('申请：新增 %d 份，共 %d 份' % (created, len(by_person)))

    # 审核通过前 4 人（触发自动入轮候），保留 1 份待审
    approved = 0
    for p in people[:4]:
        a = by_person.get(p['id'])
        if not a:
            continue
        if a.get('applicationStatus') in ('APPROVED', 'REVIEWING', 'PENDING'):
            st, r = call('/applications/%s/review' % a['id'], 'POST',
                         {'reviewResult': 'PASS', 'reviewRemark': '一期示范-审核通过'}, tok)
            if (r or {}).get('code') == 'BP00000':
                approved += 1
            else:
                print('  审核失败(%s)：%s' % (p.get('realName') or p.get('personName'),
                                          msg((st, r))))
    print('审核通过：%d 份' % approved)

    # ---------- 6) 轮候校验 ----------
    st, r = call('/allocation/waiting?pageNum=1&pageSize=200&securityType=PUBLIC', token=tok)
    waiting = (d((st, r)) or {}).get('rows') or []
    print('轮候池：%d 人（审核通过应自动入队）' % len(waiting))

    # ---------- 7) 批次 + 房源 + 状态 ----------
    st, r = call('/allocation/batches?pageNum=1&pageSize=100', token=tok)
    batch = next((x for x in (d((st, r)) or {}).get('rows') or []
                  if x.get('batchName') == TAG + '配租批次'), None)
    if not batch:
        st, r = call('/allocation/batches', 'POST',
                     {'batchName': TAG + '配租批次', 'orgId': org_id,
                      'securityType': 'PUBLIC', 'batchType': 'LOTTERY',
                      'remark': '一期示范数据'}, tok)
        batch = d((st, r))
    if not batch:
        print('批次创建失败：', msg((st, r)))
        return 1
    bid = batch['id']
    print('批次：%s（%s）' % (batch.get('batchName'), batch.get('batchStatus')))

    vacant = [h['id'] for h in houses if h.get('houseStatus') == 'VACANT'][:4]
    if vacant:
        st, r = call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': vacant}, tok)
        print('  批次加房源 %d 套：%s' % (len(vacant), msg((st, r))))

    for target in ('PUBLISHED', 'SIGNUP', 'LOTTERY'):
        st, r = call('/allocation/batches/%s/status' % bid, 'POST',
                     {'batchStatus': target}, tok)
        if (r or {}).get('code') != 'BP00000':
            print('  状态→%s 失败：%s' % (target, msg((st, r))))
    st, r = call('/allocation/batches/%s' % bid, token=tok)
    print('  批次状态：%s' % (d((st, r)) or {}).get('batchStatus'))

    # ---------- 8) 摇号 ----------
    st, r = call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'phase1'}, tok)
    print('摇号：%s' % msg((st, r)))
    st, r = call('/allocation/lottery/%s' % bid, token=tok)
    winners = d((st, r)) or []
    print('  中签记录：%d 条' % len(winners))

    # ---------- 9) 公示 ----------
    st, r = call('/publicities?pageNum=1&pageSize=100', token=tok)
    pub = next((x for x in (d((st, r)) or {}).get('rows') or []
                if x.get('title') == TAG + '配租结果公示'), None)
    if not pub:
        today = date.today()
        st, r = call('/publicities', 'POST',
                     {'publicityType': 'ALLOCATION', 'orgId': org_id, 'batchId': bid,
                      'title': TAG + '配租结果公示',
                      'content': '本期配租摇号结果公示，公示期 7 天。',
                      'startDate': str(today),
                      'endDate': str(today + timedelta(days=7))}, tok)
        pub = d((st, r))
        print('公示：%s' % msg((st, r)))
    if pub:
        st, r = call('/publicities/%s/winners' % pub['id'], token=tok)
        print('  公示中签名单：%d 条' % len(d((st, r)) or []))

    print('\n阶段完成。合同与收费见 _seed_phase1_part2.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
