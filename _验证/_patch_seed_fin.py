# -*- coding: utf-8 -*-
"""补：押金与收款（合同签约后），形成完整收费闭环。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_seed_phase1_part2.py')
s = io.open(P, encoding='utf-8').read()

anchor = "    print('\\n一期示范数据就绪。')"
if anchor not in s:
    raise SystemExit('未找到结尾锚点')

extra = '''    # ---------- 10) 押金 + 收款 ----------
    eff_contracts = [c for c in rows_of(call('/contracts?pageNum=1&pageSize=200'
                                            '&orgId=%s' % org_id, token=tok))
                     if c.get('contractStatus') == 'EFFECTIVE'][:3]
    deposits, payments = 0, 0
    for c in eff_contracts:
        st, r = call('/fin/deposits', 'POST',
                     {'contractId': c['id'], 'personId': c.get('lesseePersonId'),
                      'depositAmount': c.get('depositAmount') or 1000,
                      'paidAmount': c.get('depositAmount') or 1000,
                      'capAmount': c.get('depositAmount') or 1000,
                      'isExempt': 0}, tok)
        if ok((st, r)):
            deposits += 1

        st, r = call('/fin/payments', 'POST',
                     {'orgId': org_id, 'personId': c.get('lesseePersonId'),
                      'payerName': c.get('lesseeName') or TAG,
                      'payAmount': (c.get('monthlyRent') or 1000),
                      'payChannel': 'BANK', 'tradeNo': 'P1-' + str(c['id'])[-8:],
                      'remark': TAG + '演示收款'}, tok)
        if ok((st, r)):
            payments += 1
    print('押金：%d 笔，收款：%d 笔' % (deposits, payments))

'''
s = s.replace(anchor, extra + anchor, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已加押金与收款步骤')
