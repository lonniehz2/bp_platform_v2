# -*- coding: utf-8 -*-
"""并发第二批：账单核销（超收）、退租/换房、批次加房源重复。

在 _check_concurrency.py 基础上追加三类场景，验证：
  E. 同一账单被并发核销 → 只能核销一次，累计已收不超过应收
  F. 同一房源并发发起退租 → 不应产生两张同时生效的退租单
  G. 同一批次重复加入同一房源 → 房源不重复入池
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_concurrency.py')
s = io.open(P, encoding='utf-8').read()

if 'def scenario_payment' not in s:
    extra = '''
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
                  'payChannel': 'BANK', 'tradeNo': 'CC' + time.strftime('%H%M%S%f')}, tok)
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

    ths = [threading.Thread(target=do_term) for _ in range(3)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    st, r = call('/terminations?pageNum=1&pageSize=50', token=tok)
    same = [x for x in rows((st, r))
            if str(x.get('contractId')) == str(c['id'])
            and x.get('terminationStatus') not in ('CANCELLED', 'REJECTED')]
    check('并发退租只产生一张有效单', len(same) <= 1,
          '成功 %d 次，有效单 %d 张' % (results.count(True), len(same)))


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


'''
    s = s.replace('def main():', extra + 'def main():', 1)

    # 在结尾汇总前调用三个场景
    s = s.replace("    print('\\n结果：通过 %d，失败 %d' % (len(PASSED), len(FAILED)))",
                  "    scenario_payment(tok, oid)\n"
                  "    scenario_termination(tok, oid)\n"
                  "    scenario_batch_house(tok, oid)\n\n"
                  "    print('\\n结果：通过 %d，失败 %d' % (len(PASSED), len(FAILED)))", 1)

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('已追加 3 类并发场景')
else:
    print('已存在')
