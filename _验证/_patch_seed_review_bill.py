# -*- coding: utf-8 -*-
"""补 _seed_phase1_part2.py：
1) 申请先「受理」再走 ACCEPT → FORM → JOINT → FINAL 四阶段审核
2) 出账改用 /fin/bills/generate-batch 的正确入参（items + 起止日 + 到期日）
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_seed_phase1_part2.py')
s = io.open(P, encoding='utf-8').read()

# ---- 1) 审核段落替换 ----
start = s.find('    # ---------- 4) 审核通过（触发自动入轮候）----------')
end = s.find("    waiting = rows_of(")
if start < 0 or end < 0:
    raise SystemExit('未找到审核段落')

new_review = '''    # ---------- 4) 受理 → 四阶段审核（触发自动入轮候）----------
    STAGES = ('ACCEPT', 'FORM', 'JOINT', 'FINAL')
    passed = 0
    for p in persons[:4]:
        a = by_person.get(p['id'])
        if not a:
            continue
        aid = a['id']
        st, r = call('/applications/%s' % aid, token=tok)
        cur = (d((st, r)) or {}).get('applicationStatus')

        if cur == 'SUBMITTED':
            st, r = call('/applications/%s/accept' % aid, 'POST', {}, tok)
            if not ok((st, r)):
                print('  受理失败(%s)：%s' % (p.get('realName'), msg((st, r))))
                continue
            cur = (d((st, r)) or {}).get('applicationStatus')

        for stage in STAGES:
            if cur == 'APPROVED':
                break
            st, r = call('/applications/%s/review' % aid, 'POST',
                         {'stage': stage, 'result': 'PASS',
                          'opinion': '一期示范-%s 通过' % stage}, tok)
            if not ok((st, r)):
                print('  审核%s失败(%s)：%s' % (stage, p.get('realName'), msg((st, r))))
                break
            cur = (d((st, r)) or {}).get('applicationStatus')

        if cur == 'APPROVED':
            passed += 1
    print('审核通过：%d' % passed)

'''
s = s[:start] + new_review + s[end:]

# ---- 2) 出账段落替换 ----
bstart = s.find('    # ---------- 9) 收费 ----------')
bend = s.find("    print('\\n一期示范数据就绪。')")
if bstart < 0 or bend < 0:
    raise SystemExit('未找到收费段落')

new_bill = '''    # ---------- 9) 收费：批量出账 ----------
    st, r = call('/fin/fee-items?pageNum=1&pageSize=20', token=tok)
    fee_items = rows_of((st, r))
    rent_item = next((x for x in fee_items
                      if (x.get('feeItemName') or '').find('租金') >= 0), None) \\
        or (fee_items[0] if fee_items else None)
    if rent_item:
        today = date.today()
        st, r = call('/fin/bills/generate-batch', 'POST',
                     {'items': [{'feeItemId': rent_item['id']}],
                      'periodStart': str(today.replace(day=1)),
                      'periodEnd': str(today),
                      'billPeriod': today.strftime('%Y%m'),
                      'dueDate': str(today + timedelta(days=15)),
                      'orgId': org_id,
                      'contractIds': []}, tok)
        print('批量出账：%s' % msg((st, r)))
        gen = d((st, r)) or {}
        if isinstance(gen, dict):
            print('  生成账单：%s 张' % (gen.get('generated') or gen.get('count') or 0))
    else:
        print('批量出账：跳过（无收费项目）')

    bills = rows_of(call('/fin/bills?pageNum=1&pageSize=5&orgId=%s' % org_id, token=tok))
    print('账单核对：%s' % ('%d 条' % len(bills) if bills else '未生成'))

'''
s = s[:bstart] + new_bill + s[bend:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已更新审核与出账逻辑')
