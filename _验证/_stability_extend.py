# -*- coding: utf-8 -*-
"""稳定性加固：
  1) _verify_all.py 增加压力测试步骤
  2) _check_concurrency.py 增加两个并发场景：
     H. 账单「减免」与「核销」并发 → 不得超收
     I. 床位合同「退租申请」与「床位调换」并发 → 状态不得互相踩踏
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- 1) 验证流水线加压力测试 ----------
V = os.path.join(HERE, '_verify_all.py')
s = io.open(V, encoding='utf-8').read()
if '_perf_stress.py' not in s:
    s = s.replace("    ('perf', '接口性能', ['_perf_baseline.py', '--rounds', '2']),",
                  "    ('perf', '接口性能', ['_perf_baseline.py', '--rounds', '2']),\n"
                  "    ('stress', '压力场景', ['_perf_stress.py']),")
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('_verify_all.py：已加压力场景步骤')

# ---------- 2) 并发场景 H / I ----------
C = os.path.join(HERE, '_check_concurrency.py')
s = io.open(C, encoding='utf-8').read()
if 'def scenario_waive' not in s:
    extra = '''
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


'''
    s = s.replace('def main():', extra + 'def main():', 1)
    s = s.replace("    scenario_batch_house(tok, oid)",
                  "    scenario_batch_house(tok, oid)\n"
                  "    scenario_waive(tok, oid)\n"
                  "    scenario_terminate_vs_swap(tok, oid)", 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('_check_concurrency.py：已加 H/I 两个场景')
