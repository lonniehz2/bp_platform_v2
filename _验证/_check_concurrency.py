# -*- coding: utf-8 -*-
"""并发与边界验证：同一资源被并发操作时系统是否守住一致性。

场景：
  A. 两个操作员同时给「同一房源」签约 → 只能有一个成功（防一房多签）
  B. 同一条抄表读数重复出账 → 第二次必须被拒
  C. 同一批次重复摇号 → 第二次必须被拒或结果不变
  D. 同一申请重复终审 → 第二次必须被拒（幂等）

用法：python _check_concurrency.py
"""
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
ORG_NAME = '一期示范小区'
TAG = '并发' + time.strftime('%m%d%H%M%S')

PASSED, FAILED = [], []


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
            return e.code, {}
    except Exception as e:
        return 0, {'message': type(e).__name__}


def d(resp):
    return (resp[1] or {}).get('data')


def ok(resp):
    return (resp[1] or {}).get('code') == 'BP00000'


def rows(resp):
    data = d(resp)
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


def check(name, cond, detail=''):
    if cond:
        PASSED.append(name)
        print('  ✔ %s' % name)
    else:
        FAILED.append('%s %s' % (name, detail))
        print('  ✘ %s  %s' % (name, detail))


def main():
    tok = d(call('/auth/login', 'POST',
                 {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'}))['token']
    org = next((x for x in rows(call('/orgs?pageNum=1&pageSize=100', token=tok))
                if x['orgName'] == ORG_NAME), None)
    if not org:
        print('未找到 %s' % ORG_NAME)
        return 1
    oid = org['id']

    # 准备：两套空置房源 + 两个人
    tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
    flat = []

    def walk(ns):
        for n in ns or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
    room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)

    def new_house(tag):
        st, r = call('/houses', 'POST',
                     {'orgId': oid, 'spaceId': room['id'],
                      'houseCode': 'C-%s-%s' % (tag, time.strftime('%H%M%S')),
                      'houseName': '%s%s房' % (TAG, tag), 'houseType': 'PUBLIC_RENTAL',
                      'useType': 'CIVIL', 'area': 50, 'rentStandard': 12,
                      'rentUnit': 'AREA_MONTH', 'houseStatus': 'VACANT'}, tok)
        return d((st, r))

    def new_person(tag):
        W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        seq = str(int(time.time() * 1000))[-3:]
        base = '33010619900101' + tag + seq
        base = base[:17]
        idc = base + '10X98765432'[sum(int(base[i]) * W[i] for i in range(17)) % 11]
        st, r = call('/persons', 'POST',
                     {'personName': '%s%s' % (TAG, tag), 'idCard': idc,
                      'phone': '138%08d' % (int(time.time() * 1000) % 100000000),
                      'orgId': oid, 'householdType': 'URBAN'}, tok)
        return d((st, r))

    h1 = new_house('A')
    p1 = new_person('1')
    p2 = new_person('2')
    if not (h1 and p1 and p2):
        print('准备数据失败：', h1, p1, p2)
        return 1

    # ---------- A. 同一房源并发签约 ----------
    print('A. 同一房源并发签约（防一房多签）')
    results = {}

    def sign_flow(idx, person_id):
        st, r = call('/contracts/quick-sign', 'POST',
                     {'personId': person_id, 'houseId': h1['id'],
                      'leaseStart': str(date.today()),
                      'leaseEnd': str(date.today() + timedelta(days=180)),
                      'monthlyRent': 700, 'depositAmount': 700,
                      'securityType': 'PUBLIC', 'remark': TAG + '并发'}, tok)
        cid = (d((st, r)) or {}).get('id')
        signed = False
        if cid:
            for path, body in (('/contracts/%s/submit-sign' % cid, {}),
                               ('/contracts/%s/start-signing' % cid, {}),
                               ('/contracts/%s/sign' % cid,
                                {'signType': 'ELECTRONIC', 'reason': TAG})):
                s2, r2 = call(path, 'POST', body, tok)
                if 'sign' in path.split('/')[-1]:
                    signed = ok((s2, r2))
        results[idx] = {'contractId': cid, 'signed': signed}

    threads = [threading.Thread(target=sign_flow, args=(i, p))
               for i, p in enumerate([p1['id'], p2['id']])]
    [t.start() for t in threads]
    [t.join() for t in threads]
    signed_count = sum(1 for v in results.values() if v['signed'])
    check('并发签约只允许一个成功', signed_count == 1,
          '成功 %d 个：%s' % (signed_count, results))

    # 房源占用状态核对
    st, r = call('/houses/%s' % h1['id'], token=tok)
    status = (d((st, r)) or {}).get('houseStatus')
    check('房源状态为已占用', status in ('OCCUPIED', 'ALLOCATED'), str(status))

    # ---------- B. 抄表重复出账 ----------
    print('B. 同一条抄表读数重复出账')
    items = rows(call('/fin/fee-items?pageNum=1&pageSize=50', token=tok))
    meter = [x for x in items if x.get('calcMode') == 'METER']
    if meter and h1:
        base = 8000 + int(time.time()) % 500
        call('/fin/meter-readings', 'POST',
             {'houseId': h1['id'], 'feeItemId': meter[0]['id'], 'reading': base,
              'readDate': str(date.today() - timedelta(days=10))}, tok)
        st, r = call('/fin/meter-readings', 'POST',
                     {'houseId': h1['id'], 'feeItemId': meter[0]['id'],
                      'reading': base + 50, 'readDate': str(date.today())}, tok)
        rid = (d((st, r)) or {}).get('id')
        if rid:
            first = ok(call('/fin/meter-readings/%s/bill' % rid, 'POST', None, tok))
            second = ok(call('/fin/meter-readings/%s/bill' % rid, 'POST', None, tok))
            check('抄表出账幂等（二次被拒）', first and not second,
                  'first=%s second=%s' % (first, second))
        else:
            check('抄表出账幂等（二次被拒）', False, '读数录入失败')

    # ---------- C. 重复摇号 ----------
    print('C. 同一批次重复摇号')
    st, r = call('/allocation/batches', 'POST',
                 {'batchName': TAG + '批次', 'orgId': oid, 'securityType': 'PUBLIC',
                  'batchType': 'LOTTERY'}, tok)
    bid = (d((st, r)) or {}).get('id')
    if bid:
        vacant = [h1['id']]
        call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': vacant}, tok)
        for target in ('PUBLISHED', 'SIGNUP', 'LOTTERY'):
            call('/allocation/batches/%s/status' % bid, 'POST', {'batchStatus': target}, tok)
        first = ok(call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'a'}, tok))
        second = ok(call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'a'}, tok))
        check('重复摇号被拒绝', first and not second,
              'first=%s second=%s' % (first, second))
    else:
        check('重复摇号被拒绝', False, '批次创建失败')

    # ---------- D. 重复终审 ----------
    print('D. 同一申请重复终审')
    st, r = call('/applications?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok)
    approved = [a for a in rows((st, r)) if a.get('applicationStatus') == 'APPROVED']
    if approved:
        aid = approved[0]['id']
        again = call('/applications/%s/review' % aid, 'POST',
                     {'stage': 'FINAL', 'result': 'PASS', 'opinion': TAG}, tok)
        check('已通过申请再次终审被拒', not ok(again), (again[1] or {}).get('message', '')[:40])
    else:
        check('已通过申请再次终审被拒', False, '没有已通过的申请')

    print('\n结果：通过 %d，失败 %d' % (len(PASSED), len(FAILED)))
    for f in FAILED:
        print('  ✘ ' + f)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
