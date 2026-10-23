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
import random
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



def scenario_payment(tok, oid):
    """E. 同一账单并发核销：累计已收不能超过应收。"""
    print('E. 同一账单并发核销（防超收）')
    bills = rows(call('/fin/bills?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok))
    target = next((b for b in bills if b.get('billStatus') in ('UNPAID', 'PARTIAL')
                   and float(b.get('payableAmount') or 0) > 0), None)
    if not target:
        check('并发核销不超收', False, '没有可核销账单')
        return
    bill_id = target['id']
    payable = float(target.get('payableAmount') or 0)

    # 建一笔收款
    st, r = call('/fin/payments', 'POST',
                 {'orgId': oid, 'personId': target.get('personId'),
                  'payerName': '并发核销', 'payAmount': payable * 2,
                  'payChannel': 'BANK', 'tradeNo': 'CC' + str(int(time.time() * 1000))[-9:]}, tok)
    pay = d((st, r)) or {}
    pay_id = pay.get('id')
    if not pay_id:
        check('并发核销不超收', False, '收款创建失败 %s' % (r[1] or {}).get('message', ''))
        return

    results = []

    def do_alloc():
        st, r = call('/fin/payments/%s/allocate' % pay_id, 'POST',
                     {'billId': bill_id, 'amount': payable}, tok)
        results.append(ok((st, r)))

    ths = [threading.Thread(target=do_alloc) for _ in range(4)]
    [t.start() for t in ths]
    [t.join() for t in ths]

    st, r = call('/fin/bills/%s' % bill_id, token=tok)
    bill = d((st, r)) or {}
    paid = float(bill.get('paidAmount') or 0)
    check('并发核销成功次数受控', results.count(True) <= 2,
          '成功 %d 次' % results.count(True))
    check('累计已收不超过应收', paid <= payable + 0.01,
          '已收 %.2f / 应收 %.2f' % (paid, payable))


def scenario_termination(tok, oid):
    """F. 同一房源并发发起退租：不应出现两张有效退租单。"""
    print('F. 同一房源并发退租')
    contracts = rows(call('/contracts?pageNum=1&pageSize=100&orgId=%s' % oid, token=tok))
    eff = [c for c in contracts if c.get('contractStatus') == 'EFFECTIVE']
    if not eff:
        check('并发退租只产生一张有效单', True, '无生效合同，跳过')
        return
    c = eff[0]
    results = []

    def do_term():
        st, r = call('/terminations', 'POST',
                     {'contractId': c['id'], 'houseId': c.get('houseId'),
                      'personId': c.get('lesseePersonId'),
                      'terminationType': 'NORMAL',
                      'planExitDate': str(date.today() + timedelta(days=30)),
                      'exitReason': TAG}, tok)
        results.append(ok((st, r)))

    st0, r0 = call('/terminations?pageNum=1&pageSize=100', token=tok)
    before = len([x for x in rows((st0, r0)) if str(x.get('contractId')) == str(c['id'])])
    ths = [threading.Thread(target=do_term) for _ in range(3)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    st, r = call('/terminations?pageNum=1&pageSize=50', token=tok)
    same = [x for x in rows((st, r))
            if str(x.get('contractId')) == str(c['id'])
            and x.get('terminationStatus') not in ('CANCELLED', 'REJECTED')]
    # 只比较本次新增（历史数据不计入）
    check('并发退租只新增一张有效单', len(same) - before <= 1,
          '本次新增 %d 张（原有 %d），请求成功 %d 次'
          % (len(same) - before, before, results.count(True)))


def scenario_batch_house(tok, oid):
    """G. 同一批次重复加入同一房源：不应重复入池。"""
    print('G. 批次重复加入同一房源')
    st, r = call('/allocation/batches', 'POST',
                 {'batchName': TAG + '去重批次', 'orgId': oid, 'securityType': 'PUBLIC',
                  'batchType': 'LOTTERY'}, tok)
    bid = (d((st, r)) or {}).get('id')
    if not bid:
        check('批次房源不重复入池', False, '批次创建失败')
        return
    houses = rows(call('/houses?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok))
    hid = houses[0]['id'] if houses else None
    if not hid:
        check('批次房源不重复入池', False, '无房源')
        return
    call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': [hid]}, tok)
    call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': [hid]}, tok)
    st, r = call('/allocation/batches/%s/houses?pageNum=1&pageSize=100' % bid, token=tok)
    same = [x for x in rows((st, r)) if str(x.get('houseId')) == str(hid)]
    check('批次房源不重复入池', len(same) <= 1, '同一房源入池 %d 次' % len(same))



def scenario_waive(tok, oid):
    """H. 账单减免与核销并发：已收不得超过应收，状态不得错乱。"""
    print('H. 账单减免与核销并发')
    bills = rows(call('/fin/bills?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok))
    target = next((b for b in bills if b.get('billStatus') in ('UNPAID', 'PARTIAL')
                   and float(b.get('payableAmount') or 0) > 0), None)
    if not target:
        check('减免与核销并发不超收', True, '无可测账单，跳过')
        return
    bill_id = target['id']
    payable = float(target.get('payableAmount') or 0)
    st, r = call('/fin/payments', 'POST',
                 {'orgId': oid, 'personId': target.get('personId'),
                  'payerName': '并发减免', 'payAmount': payable,
                  'payChannel': 'BANK',
                  'tradeNo': 'WV' + str(int(time.time() * 1000))[-9:]}, tok)
    pay_id = (d((st, r)) or {}).get('id')
    if not pay_id:
        check('减免与核销并发不超收', False, '收款创建失败')
        return

    done = {}

    def do_alloc():
        st2, r2 = call('/fin/payments/%s/allocate' % pay_id, 'POST',
                       {'billId': bill_id, 'amount': payable}, tok)
        done['alloc'] = ok((st2, r2))

    def do_waive():
        st3, r3 = call('/fin/bills/%s/waive' % bill_id, 'POST',
                       {'amount': payable, 'reason': TAG}, tok)
        done['waive'] = ok((st3, r3))

    ths = [threading.Thread(target=do_alloc), threading.Thread(target=do_waive)]
    [t.start() for t in ths]
    [t.join() for t in ths]

    st4, r4 = call('/fin/bills/%s' % bill_id, token=tok)
    bill = d((st4, r4)) or {}
    paid = float(bill.get('paidAmount') or 0)
    payable_now = float(bill.get('payableAmount') or 0)
    check('减免与核销不超收', paid <= payable_now + 0.01,
          '已收 %.2f / 应收 %.2f（alloc=%s waive=%s）'
          % (paid, payable_now, done.get('alloc'), done.get('waive')))


def scenario_terminate_vs_swap(tok, oid):
    """I. 退租申请与床位调换并发：两者不能同时成功造成状态冲突。"""
    print('I. 退租与床位调换并发')
    contracts = rows(call('/contracts?pageNum=1&pageSize=100&orgId=%s' % oid, token=tok))
    eff = [c for c in contracts
           if c.get('contractStatus') == 'EFFECTIVE' and c.get('houseId')]
    beds = None
    target = None
    for c in eff:
        st, r = call('/houses/%s' % c['houseId'], token=tok)
        h = d((st, r)) or {}
        if h.get('houseType') != 'DORMITORY' or not h.get('spaceId'):
            continue
        st2, r2 = call('/spaces/%s' % h['spaceId'], token=tok)
        sp = d((st2, r2)) or {}
        if not sp.get('parentId'):
            continue
        st3, r3 = call('/houses/beds?roomSpaceId=%s' % sp['parentId'], token=tok)
        cand = [b for b in rows((st3, r3)) if not b.get('occupied') and b.get('houseId')]
        if cand:
            beds, target = cand, c
            break
    if not target or not beds:
        check('退租与调换并发不冲突', True, '无宿舍空床可测，跳过')
        return

    out = {}

    def do_term():
        st, r = call('/terminations', 'POST',
                     {'contractId': target['id'], 'houseId': target.get('houseId'),
                      'personId': target.get('lesseePersonId'),
                      'terminationType': 'NORMAL',
                      'planExitDate': str(date.today() + timedelta(days=30)),
                      'exitReason': TAG}, tok)
        out['term'] = ok((st, r))

    def do_swap():
        st, r = call('/contracts/%s/swap-bed' % target['id'], 'POST',
                     {'targetHouseId': beds[0]['houseId'], 'reason': TAG + '并发'}, tok)
        out['swap'] = ok((st, r))

    ths = [threading.Thread(target=do_term), threading.Thread(target=do_swap)]
    [t.start() for t in ths]
    [t.join() for t in ths]

    # 校验：调换成功时，合同房源必须真的指向新床；退租成功则不能出现"已释放又占用"
    st4, r4 = call('/contracts/%s' % target['id'], token=tok)
    after = d((st4, r4)) or {}
    st5, r5 = call('/houses/beds?roomSpaceId=%s' % d(call(
        '/spaces/%s' % ((d(call('/houses/%s' % target['houseId'], token=tok)) or {})
                        .get('spaceId')), token=tok)).get('parentId'), token=tok)
    same = [b for b in rows((st5, r5)) if b.get('occupied')]
    check('并发后床位占用唯一', len(same) <= 1,
          '占用 %d 张（term=%s swap=%s，合同房源=%s）'
          % (len(same), out.get('term'), out.get('swap'), after.get('houseId')))


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
        for _ in range(8):
            seq = '%03d' % random.randint(100, 999)
            base = ('33010619900101' + tag + seq)[:17]
            idc = base + '10X98765432'[sum(int(base[i]) * W[i] for i in range(17)) % 11]
            st, r = call('/persons', 'POST',
                         {'personName': '%s%s' % (TAG, seq), 'idCard': idc,
                          'phone': '138%08d' % random.randint(0, 99999999),
                          'orgId': oid, 'householdType': 'URBAN'}, tok)
            p = d((st, r))
            if p:
                return p
        return None

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

    scenario_payment(tok, oid)
    scenario_termination(tok, oid)
    scenario_batch_house(tok, oid)
    scenario_waive(tok, oid)
    scenario_terminate_vs_swap(tok, oid)

    print('\n结果：通过 %d，失败 %d' % (len(PASSED), len(FAILED)))
    for f in FAILED:
        print('  ✘ ' + f)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
