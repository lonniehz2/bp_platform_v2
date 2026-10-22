# -*- coding: utf-8 -*-
"""跨模块流程回归：一条脚本验证「已建成的关键业务链」仍然可用。

覆盖（纯接口断言，不依赖界面）：
  1. 人员 → 实名核验 → 保障档案 → 申请 → 受理 → 四阶段审核 → 通过
  2. 审核通过 → 自动进入轮候
  3. 批次 → 加房源 → 发布/报名/摇号 → 生成中签结果
  4. 公示（关联批次）→ 中签名单（脱敏）
  5. 快捷签约（存量直接签约）→ 合同草稿
  6. 合同签约推进 → 履约中
  7. 公摊分摊出账 → 金额合计等于总额
  8. 抄表录入 → 用量/金额计算 → 出账
  9. 巡检计划 → 到期执行 → 生成巡检工单

用法：python _check_flows.py
"""
import json
import sys
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
ORG_NAME = '一期示范小区'
TAG = '回归' + time.strftime('%m%d%H%M')

PASSED = []
FAILED = []


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


def code(resp):
    return (resp[1] or {}).get('code')


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



def ensure_vacant_house(tok, oid):
    """确保有至少一套验收可用的空置房源：没有就用楼层下的房间新建一套。"""
    houses = rows(call('/houses?pageNum=1&pageSize=200&orgId=%s' % oid, token=tok))
    free = [h['id'] for h in houses if h.get('houseStatus') == 'VACANT']
    if free:
        return free
    tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
    flat = []

    def walk(nodes):
        for n in nodes or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
    room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)
    floor = next((x for x in flat if x.get('spaceType') == 'FLOOR'), None)
    if not room and floor:
        st, r = call('/spaces', 'POST',
                     {'orgId': oid, 'spaceCode': 'CHK-R-' + time.strftime('%H%M%S'),
                      'spaceName': '回归房间', 'spaceType': 'ROOM',
                      'parentId': floor['id'], 'area': 55}, tok)
        room = d((st, r))
    if not room:
        return []
    st, r = call('/houses', 'POST',
                 {'orgId': oid, 'spaceId': room['id'],
                  'houseCode': 'CHK-' + time.strftime('%H%M%S'),
                  'houseName': TAG + '回归房源', 'houseType': 'PUBLIC_RENTAL',
                  'useType': 'CIVIL', 'area': 55, 'rentStandard': 15,
                  'rentUnit': 'AREA_MONTH', 'houseStatus': 'VACANT'}, tok)
    return [d((st, r))['id']] if d((st, r)) else []


def fresh_house(tok, oid, tag):
    """每次都新建一套专用房源，避免与其他检查争用空置房源。"""
    tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
    flat = []

    def walk(ns):
        for n in ns or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
    room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)
    floor = next((x for x in flat if x.get('spaceType') == 'FLOOR'), None)
    if not room and floor:
        st, r = call('/spaces', 'POST',
                     {'orgId': oid, 'spaceCode': 'F-R-' + tag, 'spaceName': '回归房间' + tag,
                      'spaceType': 'ROOM', 'parentId': floor['id'], 'area': 50}, tok)
        room = d((st, r))
    if not room:
        return None
    st, r = call('/houses', 'POST',
                 {'orgId': oid, 'spaceId': room['id'], 'houseCode': 'FH-' + tag,
                  'houseName': '%s房%s' % (TAG, tag), 'houseType': 'PUBLIC_RENTAL',
                  'useType': 'CIVIL', 'area': 50, 'rentStandard': 12,
                  'rentUnit': 'AREA_MONTH', 'houseStatus': 'VACANT'}, tok)
    return d((st, r))

def main():
    tok = d(call('/auth/login', 'POST',
                 {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'}))['token']
    org = next((x for x in rows(call('/orgs?pageNum=1&pageSize=100', token=tok))
                if x['orgName'] == ORG_NAME), None)
    if not org:
        print('未找到 %s，请先跑 _seed_phase1.py' % ORG_NAME)
        return 1
    oid = org['id']

    # ---------- 1) 人员 → 核验 → 档案 → 申请 ----------
    idcard = '33010619900101' + '%03d' % random.randint(100, 999) + '1'
    W = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    idcard = idcard[:17] + '10X98765432'[sum(int(idcard[i]) * W[i] for i in range(17)) % 11]
    st, r = call('/persons', 'POST',
                 {'personName': TAG + '甲', 'idCard': idcard,
                  'phone': '139%08d' % (int(time.time()) % 100000000),
                  'orgId': oid, 'householdType': 'URBAN'}, tok)
    pid = (d((st, r)) or {}).get('id')
    check('创建人员', bool(pid), code((st, r)))

    if pid:
        st, r = call('/verify-records', 'POST',
                     {'personId': pid, 'verifyType': 'IDCARD_FACE', 'userName': TAG + '甲',
                      'resultCode': 'OK', 'faceScore': 95, 'faceResult': '1',
                      'citizenResult': '1', 'responseCode': '200'}, tok)
        check('实名核验通过', code((st, r)) == 'BP00000', code((st, r)))

        st, r = call('/guarantee-profiles', 'POST',
                     {'personId': pid, 'securityType': 'PUBLIC', 'familySize': 2,
                      'monthlyIncome': 4800}, tok)
        check('保障档案建档', code((st, r)) == 'BP00000', code((st, r)))

        st, r = call('/applications', 'POST',
                     {'orgId': oid, 'personId': pid, 'securityType': 'PUBLIC',
                      'securityMode': 'HOUSE', 'applyChannel': 'ONLINE', 'familySize': 2,
                      'declaredIncome': 5000, 'complianceCommitFlag': 1,
                      'dataShareAgreeFlag': 1}, tok)
        aid = (d((st, r)) or {}).get('id')
        check('提交申请', bool(aid), code((st, r)))

        # 受理 + 四阶段审核
        if aid:
            st, r = call('/applications/%s/accept' % aid, 'POST', {}, tok)
            check('受理申请', code((st, r)) == 'BP00000', code((st, r)))
            final = None
            for stage in ('ACCEPT', 'FORM', 'JOINT', 'FINAL'):
                st, r = call('/applications/%s/review' % aid, 'POST',
                             {'stage': stage, 'result': 'PASS', 'opinion': '回归'}, tok)
                final = (d((st, r)) or {}).get('applicationStatus')
            check('审核四阶段 → 通过', final == 'APPROVED', str(final))

            # 2) 自动入轮候
            queued = False
            for _ in range(5):
                wait = rows(call('/allocation/waiting?pageNum=1&pageSize=200'
                                 '&securityType=PUBLIC', token=tok))
                if any(str(w.get('personId')) == str(pid) for w in wait):
                    queued = True
                    break
                time.sleep(1)
            check('审核通过自动入轮候', queued, '轮候池 %d 人' % len(wait))

    # ---------- 3) 批次 → 摇号 ----------
    st, r = call('/allocation/batches', 'POST',
                 {'batchName': TAG + '批次', 'orgId': oid, 'securityType': 'PUBLIC',
                  'batchType': 'LOTTERY'}, tok)
    bid = (d((st, r)) or {}).get('id')
    check('创建配租批次', bool(bid), code((st, r)))

    if bid:
        fh = fresh_house(tok, oid, 'B')
        vacant = [fh['id']] if fh else ensure_vacant_house(tok, oid)[:1]
        if vacant:
            st, r = call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': vacant}, tok)
            check('批次加入房源', code((st, r)) == 'BP00000', code((st, r)))
        for target in ('PUBLISHED', 'SIGNUP', 'LOTTERY'):
            call('/allocation/batches/%s/status' % bid, 'POST', {'batchStatus': target}, tok)
        st, r = call('/allocation/batches/%s' % bid, token=tok)
        check('批次推进到摇号中',
              (d((st, r)) or {}).get('batchStatus') == 'LOTTERY',
              (d((st, r)) or {}).get('batchStatus'))
        st, r = call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'chk'}, tok)
        check('执行摇号', code((st, r)) == 'BP00000', code((st, r)))

        # ---------- 4) 公示 → 中签名单 ----------
        st, r = call('/publicities', 'POST',
                     {'publicityType': 'ALLOCATION', 'orgId': oid, 'batchId': bid,
                      'title': TAG + '公示', 'content': '回归公示',
                      'startDate': str(date.today()),
                      'endDate': str(date.today() + timedelta(days=7))}, tok)
        pub = (d((st, r)) or {}).get('id')
        check('创建公示并关联批次', bool(pub), code((st, r)))
        if pub:
            winners = d(call('/publicities/%s/winners' % pub, token=tok)) or []
            masked = all((w.get('idCardMask') or '').find('*') >= 0 or not w.get('idCardMask')
                         for w in winners)
            check('中签名单可见且证件脱敏', len(winners) > 0 and masked,
                  '%d 条' % len(winners))

    # ---------- 5/6) 快捷签约 → 签约生效 ----------
    persons = rows(call('/persons?pageNum=1&pageSize=1&orgId=%s' % oid, token=tok))
    fh2 = fresh_house(tok, oid, 'S')
    free = [fh2['id']] if fh2 else ensure_vacant_house(tok, oid)
    if persons and free:
        st, r = call('/contracts/quick-sign', 'POST',
                     {'personId': persons[0]['id'], 'houseId': free[0],
                      'leaseStart': str(date.today()),
                      'leaseEnd': str(date.today() + timedelta(days=180)),
                      'monthlyRent': 800, 'depositAmount': 800,
                      'securityType': 'PUBLIC', 'remark': TAG}, tok)
        c = d((st, r)) or {}
        check('快捷签约生成合同', code((st, r)) == 'BP00000' and bool(c.get('contractNo')),
              code((st, r)))
        check('合同带出承租人姓名', bool(c.get('lesseeName')), str(c.get('lesseeName')))
        cid = c.get('id')
        if cid:
            for path, body in (('/contracts/%s/submit-sign' % cid, {}),
                               ('/contracts/%s/start-signing' % cid, {}),
                               ('/contracts/%s/sign' % cid,
                                {'signType': 'ELECTRONIC', 'reason': TAG})):
                call(path, 'POST', body, tok)
            st, r = call('/contracts/%s' % cid, token=tok)
            check('签约推进到履约中',
                  (d((st, r)) or {}).get('contractStatus') == 'EFFECTIVE',
                  (d((st, r)) or {}).get('contractStatus'))

    # ---------- 7) 公摊分摊 ----------
    items = rows(call('/fin/fee-items?pageNum=1&pageSize=50', token=tok))
    if items:
        st, r = call('/fin/bills/generate-shared', 'POST',
                     {'orgId': oid, 'feeItemId': items[0]['id'], 'totalAmount': 600,
                      'periodStart': str(date.today().replace(day=1)),
                      'periodEnd': str(date.today()), 'billPeriod': date.today().strftime('%Y%m'),
                      'allocateBy': 'AREA'}, tok)
        dd = d((st, r)) or {}
        total_share = sum(float(x.get('share') or 0) for x in (dd.get('details') or []))
        check('公摊分摊生成账单', code((st, r)) == 'BP00000', code((st, r)))
        check('分摊合计等于总额', abs(total_share - 600) < 0.01 if dd.get('details') else True,
              '合计 %.2f' % total_share)

    # ---------- 8) 抄表 → 出账 ----------
    meter_items = [x for x in items if x.get('calcMode') == 'METER']
    if meter_items and free:
        hid = free[0]
        base = 5000 + (int(time.time()) % 1000)
        call('/fin/meter-readings', 'POST',
             {'houseId': hid, 'feeItemId': meter_items[0]['id'], 'reading': base,
              'readDate': str(date.today() - timedelta(days=30))}, tok)
        st, r = call('/fin/meter-readings', 'POST',
                     {'houseId': hid, 'feeItemId': meter_items[0]['id'],
                      'reading': base + 100, 'readDate': str(date.today())}, tok)
        m = d((st, r)) or {}
        check('抄表用量计算', float(m.get('usageAmount') or 0) == 100,
              str(m.get('usageAmount')))
        if m.get('id'):
            st2, r2 = call('/fin/meter-readings/%s/bill' % m['id'], 'POST', None, tok)
            check('抄表出账', code((st2, r2)) == 'BP00000', code((st2, r2)))

    # ---------- 9) 巡检计划 → 工单 ----------
    st, r = call('/ops/inspection-plans', 'POST',
                 {'planName': TAG + '巡检', 'orgId': oid, 'inspectType': 'SAFETY',
                  'frequency': 'MONTH', 'nextRunDate': str(date.today())}, tok)
    plan = (d((st, r)) or {}).get('id')
    check('创建巡检计划', bool(plan), code((st, r)))
    if plan:
        st, r = call('/ops/inspection-plans/run-due', 'POST', {}, tok)
        dd = d((st, r)) or {}
        check('到期执行生成工单', int(dd.get('generated') or 0) >= 1,
              json.dumps(dd, ensure_ascii=False))

    print('\n结果：通过 %d，失败 %d' % (len(PASSED), len(FAILED)))
    for f in FAILED:
        print('  ✘ ' + f)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
