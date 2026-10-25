# -*- coding: utf-8 -*-
"""追加两个资金并发场景：J 一单多账单核销、K 押金并发退款。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_concurrency.py')
s = io.open(P, encoding='utf-8').read()

if 'scenario_multi_bill' in s:
    print('已存在新场景')
    raise SystemExit(0)

NEW = '''
def scenario_multi_bill(tok, oid):
    """J. 同一收款单并发核销到多张账单：累计核销不得超过收款金额。"""
    print('J. 同一收款单并发核销多账单')
    bills = [b for b in rows(call('/fin/bills?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok))
             if b.get('billStatus') in ('UNPAID', 'PARTIAL')
             and float(b.get('payableAmount') or 0) > 0]
    if len(bills) < 3:
        check('一单多账单核销不超额', True, '账单不足 3 张，跳过')
        return
    picks = bills[:3]
    total_payable = sum(float(b.get('payableAmount') or 0) for b in picks)
    # 收款金额只够一张半账单，制造竞争
    pay_amount = round(total_payable * 0.5, 2)
    st, r = call('/fin/payments', 'POST',
                 {'orgId': oid, 'personId': picks[0].get('personId'),
                  'payerName': '并发多账单', 'payAmount': pay_amount,
                  'payChannel': 'BANK',
                  'tradeNo': 'MB' + str(int(time.time() * 1000))[-9:]}, tok)
    pay_id = (d((st, r)) or {}).get('id')
    if not pay_id:
        check('一单多账单核销不超额', False, '收款创建失败')
        return

    results = []

    def alloc(bill):
        st2, r2 = call('/fin/payments/%s/allocate' % pay_id, 'POST',
                       {'billId': bill['id'],
                        'amount': float(bill.get('payableAmount') or 0)}, tok)
        results.append(ok((st2, r2)))

    ths = [threading.Thread(target=alloc, args=(b,)) for b in picks]
    [t.start() for t in ths]
    [t.join() for t in ths]

    st3, r3 = call('/fin/payments/%s' % pay_id, token=tok)
    pay = d((st3, r3)) or {}
    reconciled = float(pay.get('reconciledAmount') or 0)
    check('一单多账单核销不超额', reconciled <= pay_amount + 0.01,
          '已核销 %.2f / 收款 %.2f（成功 %d 次）'
          % (reconciled, pay_amount, results.count(True)))


def scenario_refund_race(tok, oid):
    """K. 同一合同并发退还押金：累计退款不得超过押金余额。"""
    print('K. 押金并发退款不超退')
    st, r = call('/fin/deposits?pageNum=1&pageSize=20', token=tok)
    deps = [x for x in rows((st, r))
            if float(x.get('balanceAmount') or 0) > 0 and x.get('contractId')]
    if not deps:
        check('押金并发退款不超退', True, '无可用押金台账，跳过')
        return
    dep = deps[0]
    balance = float(dep.get('balanceAmount') or 0)
    contract_id = dep['contractId']
    # 每笔退一半余额，四笔并发 → 最多只能成功 2 笔
    half = round(balance / 2, 2)
    results = []

    def refund():
        st2, r2 = call('/fin/refunds', 'POST',
                       {'refundType': 'DEPOSIT', 'contractId': contract_id,
                        'personId': dep.get('personId'), 'refundAmount': half,
                        'refundReason': TAG}, tok)
        results.append(ok((st2, r2)))

    ths = [threading.Thread(target=refund) for _ in range(4)]
    [t.start() for t in ths]
    [t.join() for t in ths]

    st3, r3 = call('/fin/deposits/by-contract/%s' % contract_id, token=tok)
    dep_after = d((st3, r3)) or {}
    left = float(dep_after.get('balanceAmount') or 0)
    check('押金并发退款不超退', left >= -0.01,
          '余额 %.2f → %.2f（成功 %d 笔，每笔 %.2f）'
          % (balance, left, results.count(True), half))

'''

# 插入到 scenario_terminate_vs_swap 之前
anchor = '\ndef scenario_terminate_vs_swap(tok, oid):'
s = s.replace(anchor, NEW + anchor, 1)

# 注册到调用处
if 'scenario_multi_bill(tok' not in s.split('scenario_terminate_vs_swap(tok')[0]:
    pass

marker = '    scenario_waive(tok, oid)'
if marker in s:
    s = s.replace(marker, marker + '''
    scenario_multi_bill(tok, oid)
    scenario_refund_race(tok, oid)''', 1)
    print('已注册 J/K 场景')
else:
    print('未找到调用点，请手动注册')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('场景代码已写入')
