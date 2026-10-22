# -*- coding: utf-8 -*-
"""一期示范数据 · 完整链路（第二部分，接 _seed_phase1.py 之后）

覆盖：实名核验 → 保障档案 → 申请 → 审核通过（自动入轮候）
      → 批次(含 VACANT 房源) → 发布/报名/摇号 → 公示(关联批次)
      → 快捷签约生成合同 → 账单/收款/押金

幂等：已存在的对象复用，不重复创建。
"""
import json
import urllib.error
import urllib.parse
import urllib.request
import time
from datetime import date, timedelta

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
TAG = '一期示范'
ORG_NAME = TAG + '小区'


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


def ok(resp):
    return (resp[1] or {}).get('code') == 'BP00000'


def msg(resp):
    return '%s %s' % ((resp[1] or {}).get('code'),
                      ((resp[1] or {}).get('message') or '')[:60])


def rows_of(resp):
    data = d(resp)
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


BATCH_NAME = TAG + '配租批次' + time.strftime('%m%d%H%M')


def main():
    tok = d(call('/auth/login', 'POST',
                 {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'}))['token']
    print('登录成功')

    # 定位一期组织
    orgs = rows_of(call('/orgs?pageNum=1&pageSize=100', token=tok))
    org = next((x for x in orgs if x['orgName'] == ORG_NAME), None)
    if not org:
        print('未找到 %s，请先运行 _seed_phase1.py' % ORG_NAME)
        return 1
    org_id = org['id']

    persons = rows_of(call('/persons?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok))
    if not persons:
        allp = rows_of(call('/persons?pageNum=1&pageSize=500', token=tok))
        names = {'张一期', '李二期', '王三期', '赵四期', '钱待审', '孙退租'}
        persons = [x for x in allp if (x.get('realName') or x.get('personName')) in names]
    print('人员：%d 名' % len(persons))
    if len(persons) < 4:
        print('人员不足，请先运行 _seed_phase1.py')
        return 1

    # ---------- 1) 实名核验 ----------
    verified = 0
    for p in persons:
        st, r = call('/verify-records?pageNum=1&pageSize=5&personId=%s' % p['id'], token=tok)
        exists = rows_of((st, r))
        if any((x.get('verifyPass') in (1, '1')) or str(x.get('verifyResult') or '').startswith('通过')
               for x in exists):
            verified += 1
            continue
        st, r = call('/verify-records', 'POST',
                     {'personId': p['id'], 'verifyType': 'IDCARD_FACE',
                      'userName': p.get('realName'), 'resultCode': 'OK',
                      'faceScore': 95, 'faceResult': '1',
                      'citizenResult': '1', 'responseCode': '200'}, tok)
        if ok((st, r)):
            verified += 1
        else:
            print('  核验失败(%s)：%s' % (p.get('realName'), msg((st, r))))
    print('实名核验：%d / %d' % (verified, len(persons)))

    # ---------- 2) 保障档案 ----------
    profiled = 0
    for p in persons:
        st, r = call('/guarantee-profiles/person/%s' % p['id'], token=tok)
        if d((st, r)):
            profiled += 1
            continue
        st, r = call('/guarantee-profiles', 'POST',
                     {'personId': p['id'], 'securityType': 'PUBLIC', 'familySize': 2,
                      'familyType': 'CORE', 'monthlyIncome': 4800 + 200,
                      'assetDeclare': 0, 'hasHouse': 0, 'houseCount': 0,
                      'hasVehicle': 0, 'socialSecurity': 'CONTINUOUS'}, tok)
        if ok((st, r)):
            profiled += 1
        else:
            print('  建档失败(%s)：%s' % (p.get('realName'), msg((st, r))))
    print('保障档案：%d / %d' % (profiled, len(persons)))

    # ---------- 3) 申请 ----------
    apps = rows_of(call('/applications?pageNum=1&pageSize=200', token=tok))
    by_person = {a.get('personId'): a for a in apps}
    made = 0
    for p in persons[:5]:
        if p['id'] in by_person:
            continue
        st, r = call('/applications', 'POST',
                     {'orgId': org_id, 'personId': p['id'], 'securityType': 'PUBLIC',
                      'securityMode': 'HOUSE', 'applyChannel': 'ONLINE',
                      'familySize': 2, 'declaredIncome': 5000,
                      'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1}, tok)
        if ok((st, r)):
            by_person[p['id']] = d((st, r))
            made += 1
        else:
            print('  申请失败(%s)：%s' % (p.get('realName'), msg((st, r))))
    print('申请：新增 %d，共 %d' % (made, len(by_person)))

    # ---------- 4) 审核通过（触发自动入轮候）----------
    passed = 0
    for p in persons[:4]:
        a = by_person.get(p['id'])
        if not a:
            continue
        if a.get('applicationStatus') == 'APPROVED':
            passed += 1
            continue
        st, r = call('/applications/%s/review' % a['id'], 'POST',
                     {'stage': 'ACCEPT', 'result': 'PASS', 'opinion': '一期示范-受理通过'}, tok)
        if ok((st, r)):
            passed += 1
        else:
            print('  审核失败(%s)：%s' % (p.get('realName'), msg((st, r))))
    print('审核通过：%d' % passed)

    waiting = rows_of(call('/allocation/waiting?pageNum=1&pageSize=200&securityType=PUBLIC',
                           token=tok))
    print('轮候池：%d 人' % len(waiting))

    # ---------- 5) 批次 + 房源 ----------
    batches = rows_of(call('/allocation/batches?pageNum=1&pageSize=100', token=tok))
    batch = next((x for x in batches if x.get('batchName') == TAG + '配租批次'
                   and x.get('batchStatus') == 'DRAFT'), None)
    if not batch:
        st, r = call('/allocation/batches', 'POST',
                     {'batchName': BATCH_NAME, 'orgId': org_id,
                      'securityType': 'PUBLIC', 'batchType': 'LOTTERY'}, tok)
        batch = d((st, r))
    bid = batch['id']
    print('批次：%s（%s）' % (batch.get('batchName'), batch.get('batchStatus')))

    houses = rows_of(call('/houses?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok))
    vacant = [h['id'] for h in houses if h.get('houseStatus') in ('VACANT', None, '')][:4] or [h['id'] for h in houses[:4]]
    print('房源：%d 套（空置 %d）' % (len(houses), len(vacant)))
    if vacant:
        st, r = call('/allocation/batches/%s/houses' % bid, 'POST',
                     {'houseIds': vacant[:4]}, tok)
        print('  入池 %d 套：%s' % (len(vacant[:4]), msg((st, r))))

    for target in ('PUBLISHED', 'SIGNUP', 'LOTTERY'):
        st, r = call('/allocation/batches/%s/status' % bid, 'POST',
                     {'batchStatus': target}, tok)
        if not ok((st, r)):
            print('  状态→%s：%s' % (target, msg((st, r))))
    st, r = call('/allocation/batches/%s' % bid, token=tok)
    print('  状态：%s' % (d((st, r)) or {}).get('batchStatus'))

    # ---------- 6) 摇号 ----------
    st, r = call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'phase1'}, tok)
    print('摇号：%s' % msg((st, r)))
    results = d(call('/allocation/lottery/%s' % bid, token=tok)) or []
    print('  中签记录：%d' % len(results))

    # ---------- 7) 公示 ----------
    pubs = rows_of(call('/publicities?pageNum=1&pageSize=100', token=tok))
    pub = next((x for x in pubs if x.get('title') == TAG + '配租结果公示'), None)
    if not pub:
        today = date.today()
        st, r = call('/publicities', 'POST',
                     {'publicityType': 'ALLOCATION', 'orgId': org_id, 'batchId': bid,
                      'title': TAG + '配租结果公示', 'content': '本期配租结果公示，为期 7 天。',
                      'startDate': str(today), 'endDate': str(today + timedelta(days=7))}, tok)
        pub = d((st, r))
    if pub:
        winners = d(call('/publicities/%s/winners' % pub['id'], token=tok)) or []
        print('公示：%s，中签名单 %d 条' % (pub.get('title'), len(winners)))

    # ---------- 8) 合同（快捷签约）----------
    contracts = rows_of(call('/contracts?pageNum=1&pageSize=200', token=tok))
    existing = {c.get('lesseePersonId') for c in contracts}
    signed = 0
    for idx, p in enumerate(persons[:3]):
        if p['id'] in existing:
            signed += 1
            continue
        hs = vacant[idx] if idx < len(vacant) else None
        if not hs:
            break
        st, r = call('/contracts/quick-sign', 'POST',
                     {'personId': p['id'], 'houseId': hs,
                      'leaseStart': str(date.today()),
                      'leaseEnd': str(date.today() + timedelta(days=365)),
                      'monthlyRent': 900 + idx * 100, 'depositAmount': 1000,
                      'securityType': 'PUBLIC', 'remark': TAG + '直接签约'}, tok)
        if ok((st, r)):
            signed += 1
        else:
            print('  合同失败(%s)：%s' % (p.get('realName'), msg((st, r))))
    print('合同：%d 份（快捷签约）' % signed)

    # ---------- 9) 收费 ----------
    bills = rows_of(call('/fin/bills?pageNum=1&pageSize=1', token=tok))
    st, r = call('/fin/bills/generate-batch', 'POST',
                 {'orgId': org_id, 'billPeriod': date.today().strftime('%Y%m'),
                  'overwrite': False}, tok)
    print('批量出账：%s' % msg((st, r)))

    print('\n一期示范数据就绪。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
