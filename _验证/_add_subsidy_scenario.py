# -*- coding: utf-8 -*-
"""追加并发场景 L：同一合同同期间并发补贴发放只能成功一次。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_concurrency.py')
s = io.open(P, encoding='utf-8').read()

if 'scenario_subsidy_race' in s:
    print('已存在')
    raise SystemExit(0)

NEW = '''
def scenario_subsidy_race(tok, oid):
    """L. 同一合同同期间并发发放补贴：只能成功一条。"""
    print('L. 并发发放补贴只发一次')
    contracts = rows(call('/contracts?pageNum=1&pageSize=50&orgId=%s' % oid, token=tok))
    eff = [c for c in contracts if c.get('contractStatus') in ('ACTIVE', 'EFFECTIVE')]
    if not eff:
        check('并发补贴只发一次', True, '无生效合同，跳过')
        return
    ct = eff[0]
    period = '2099-01'   # 取未来期间，避免与已有数据冲突
    results = []

    def grant():
        st, r = call('/fin/subsidies/records', 'POST',
                     {'contractId': ct['id'], 'personId': ct.get('lesseePersonId'),
                      'subsidyPeriod': period, 'standardId': None}, tok)
        results.append(ok((st, r)))

    ths = [threading.Thread(target=grant) for _ in range(4)]
    [t.start() for t in ths]
    [t.join() for t in ths]

    st2, r2 = call('/fin/subsidies/records?pageNum=1&pageSize=50&subsidyPeriod=%s'
                   % period, token=tok)
    made = [x for x in rows((st2, r2)) if str(x.get('contractId')) == str(ct['id'])]
    check('并发补贴只发一次', len(made) <= 1,
          '成功 %d 次，落库 %d 条' % (results.count(True), len(made)))

'''

anchor = '\ndef scenario_terminate_vs_swap(tok, oid):'
s = s.replace(anchor, NEW + anchor, 1)

marker = '    scenario_refund_race(tok, oid)'
s = s.replace(marker, marker + '\n    scenario_subsidy_race(tok, oid)', 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已加场景 L 并注册')
