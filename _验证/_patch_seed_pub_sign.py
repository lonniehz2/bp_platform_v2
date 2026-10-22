# -*- coding: utf-8 -*-
"""补 _seed_phase1_part2.py：
1) 公示每次按当前批次新建（旧公示没关联批次，名单为空）
2) 快捷签约后推进签约流程（提交待签 → 开始签约 → 签约），使合同 EFFECTIVE 才可出账
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_seed_phase1_part2.py')
s = io.open(P, encoding='utf-8').read()

# ---- 1) 公示段落：改为始终按当前批次新建 ----
start = s.find('    # ---------- 7) 公示 ----------')
end = s.find('    # ---------- 8) 合同（快捷签约）----------')
if start < 0 or end < 0:
    raise SystemExit('未找到公示段落')

new_pub = '''    # ---------- 7) 公示（始终关联当前批次）----------
    today = date.today()
    st, r = call('/publicities', 'POST',
                 {'publicityType': 'ALLOCATION', 'orgId': org_id, 'batchId': bid,
                  'title': '%s配租结果公示-%s' % (TAG, batch.get('batchNo') or bid),
                  'content': '本期配租结果公示，为期 7 天，中签名单见公示明细。',
                  'startDate': str(today),
                  'endDate': str(today + timedelta(days=7))}, tok)
    pub = d((st, r))
    if pub:
        st2, r2 = call('/publicities/%s/publish' % pub['id'], 'POST', {}, tok)
        winners = d(call('/publicities/%s/winners' % pub['id'], token=tok)) or []
        print('公示：%s，中签名单 %d 条（发布：%s）'
              % (pub.get('title'), len(winners), msg((st2, r2))))
    else:
        print('公示创建失败：%s' % msg((st, r)))

'''
s = s[:start] + new_pub + s[end:]

# ---- 2) 合同段落：签约推进 ----
cstart = s.find('    # ---------- 8) 合同（快捷签约）----------')
cend = s.find('    # ---------- 9) 收费')
if cstart < 0 or cend < 0:
    raise SystemExit('未找到合同段落')

new_contract = '''    # ---------- 8) 合同：快捷签约 + 签约流程 ----------
    contracts = rows_of(call('/contracts?pageNum=1&pageSize=200', token=tok))
    existing = {c.get('lesseePersonId') for c in contracts}
    signed, activated = 0, 0
    for idx, p in enumerate(persons[:3]):
        hs = vacant[idx] if idx < len(vacant) else None
        if not hs:
            break
        c = next((x for x in contracts if x.get('lesseePersonId') == p['id']), None)
        if not c:
            st, r = call('/contracts/quick-sign', 'POST',
                         {'personId': p['id'], 'houseId': hs,
                          'leaseStart': str(date.today()),
                          'leaseEnd': str(date.today() + timedelta(days=365)),
                          'monthlyRent': 900 + idx * 100, 'depositAmount': 1000,
                          'securityType': 'PUBLIC', 'remark': TAG + '直接签约'}, tok)
            if not ok((st, r)):
                print('  合同失败(%s)：%s' % (p.get('realName'), msg((st, r))))
                continue
            c = d((st, r))
            signed += 1

        # 推进到履约中：提交待签 → 开始签约 → 签约
        cid = c['id']
        for path, body in (('/contracts/%s/submit-sign' % cid, {}),
                           ('/contracts/%s/start-signing' % cid, {}),
                           ('/contracts/%s/sign' % cid,
                            {'signType': 'ELECTRONIC', 'reason': TAG + '演示签约'})):
            st, r = call(path, 'POST', body, tok)
            if not ok((st, r)):
                print('  签约推进失败(%s %s)：%s' % (p.get('realName'), path.split('/')[-1],
                                                msg((st, r))))
                break
        st, r = call('/contracts/%s' % cid, token=tok)
        status = (d((st, r)) or {}).get('contractStatus')
        if status == 'EFFECTIVE':
            activated += 1
    print('合同：新建 %d 份，已签约生效 %d 份' % (signed, activated))

'''
s = s[:cstart] + new_contract + s[cend:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已更新公示与合同签约逻辑')
