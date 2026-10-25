# -*- coding: utf-8 -*-
"""边缘旅程：退租 / 合同变更 / 短租 / 欠费催缴。

以模块形式被 _check_journeys.py 导入调用，复用其 call/login/step。
"""
from datetime import date, timedelta


def run_edge_journeys(env):
    """env 提供 call/login/step/rows/data/rid/gen_id_card/admin。"""
    call = env['call']
    step = env['step']
    rows = env['rows']
    data = env['data']
    rid = env['rid']
    admin = env['admin']

    # ------------------------------------------------------------ 旅程7
    print('\n[旅程7] 退租：建合同 → 签约 → 申请 → 审批 → 验房 → 结算 → 释放房源')
    st, ro = call('/orgs?pageNum=1&pageSize=1', 'GET', None, admin)
    org = (rows((st, ro)) or [{}])[0].get('id')
    # 选一间没有生效合同的房源，保证脚本可重复执行
    st, rc0 = call('/contracts?pageNum=1&pageSize=300', 'GET', None, admin)
    used = {str(x.get('houseId')) for x in rows((st, rc0))
            if x.get('contractStatus') in ('ACTIVE', 'SIGNING', 'PENDING_SIGN')}
    st, rh = call('/houses?pageNum=1&pageSize=300', 'GET', None, admin)
    hs = [x for x in rows((st, rh)) if str(x.get('id')) not in used]
    house = next((x for x in hs if x.get('houseStatus') in ('AVAILABLE', 'VACANT')),
                 hs[0] if hs else {})
    st, rp = call('/persons?pageNum=1&pageSize=1', 'GET', None, admin)
    person = (rows((st, rp)) or [{}])[0]

    contract_id = None
    if org and house.get('id') and person.get('id'):
        st, rc = call('/contracts', 'POST', {
            'contractType': 'PUBLIC_RENTAL', 'orgId': org, 'lessorOrgId': org,
            'lesseePersonId': person['id'], 'lesseeName': person.get('personName'),
            'houseId': house['id'], 'spaceId': house.get('spaceId'),
            'leaseStart': str(date.today() - timedelta(days=30)),
            'leaseEnd': str(date.today() + timedelta(days=335)),
            'rentPrice': 1800, 'monthlyRent': 1800, 'rentUnit': 'HOUSE_MONTH',
            'depositAmount': 1800}, admin)
        contract = data((st, rc)) or {}
        contract_id = contract.get('id')
        step('旅程7', '创建合同', st == 200 and contract_id, (rc or {}).get('message', '')[:70])

    if contract_id:
        st, r = call('/contracts/%s/submit-sign' % contract_id, 'POST', {}, admin)
        step('旅程7', '提交签约', st == 200, (r or {}).get('message', '')[:60])
        call('/contracts/%s/start-signing' % contract_id, 'POST', {}, admin)
        st, r = call('/contracts/%s/sign' % contract_id, 'POST', {}, admin)
        step('旅程7', '完成签约', st == 200, (r or {}).get('message', '')[:60])

        st, rt = call('/terminations', 'POST', {
            'contractId': contract_id, 'houseId': house['id'],
            'personId': person['id'], 'terminationType': 'NORMAL', 'reason': '工作调动',
            'expectLeaveDate': str(date.today() + timedelta(days=15))}, admin)
        term = data((st, rt)) or {}
        tid = term.get('id')
        step('旅程7', '提交退租申请', st == 200 and tid, (rt or {}).get('message', '')[:70])

        if tid:
            st, r = call('/terminations/%s/submit' % tid, 'POST', {}, admin)
            step('旅程7', '退租单提交审批', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/terminations/%s/approve' % tid, 'POST', {}, admin)
            step('旅程7', '退租审批通过', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/terminations/%s/inspect' % tid, 'POST', {
                'inspectStatus': 'PASSED', 'inspectResult': '房屋状况良好',
                'damageAmount': 0}, admin)
            step('旅程7', '验房通过', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/terminations/%s/settle' % tid, 'POST', {
                'depositRefund': 1800, 'arrearsAmount': 0}, admin)
            step('旅程7', '退租结算', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/terminations/%s/mark-released' % tid, 'POST', {}, admin)
            step('旅程7', '标记房源已释放', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/houses/%s' % house['id'], 'GET', None, admin)
            hs2 = data((st, r)) or {}
            step('旅程7', '房源状态可查询', st == 200,
                 '当前 %s' % hs2.get('houseStatus'))

    # ------------------------------------------------------------ 旅程8
    print('\n[旅程8] 合同变更：发起变更 → 审批 → 合同生效租金')
    if contract_id:
        st, rch = call('/contracts/%s/changes' % contract_id, 'POST', {
            'changeType': 'RENT_ADJUST', 'newMonthlyRent': 1950,
            'effectiveDate': str(date.today() + timedelta(days=30)),
            'reason': '年度调价'}, admin)
        change = data((st, rch)) or {}
        cid = change.get('id')
        step('旅程8', '发起合同变更', st == 200 and cid, (rch or {}).get('message', '')[:70])
        if cid:
            st, r = call('/contract-changes/%s/approve' % cid, 'POST', {}, admin)
            step('旅程8', '变更审批通过', st == 200, (r or {}).get('message', '')[:60])

    # ------------------------------------------------------------ 旅程9
    print('\n[旅程9] 短租：下单 → 确认 → 入住 → 退房')
    if house.get('id'):
        st, rso = call('/short-rent-orders', 'POST', {
            'houseId': house['id'], 'guestName': '短租客' + rid(),
            'guestPhone': '138' + rid()[:8],
            'checkInTime': str(date.today()) + ' 00:01:00',
            'checkOutTime': str(date.today() + timedelta(days=2)) + ' 12:00:00',
            'nightlyPrice': 260, 'sourceChannel': 'WALKIN'}, admin)
        so = data((st, rso)) or {}
        sid = so.get('id')
        step('旅程9', '短租下单', st == 200 and sid, (rso or {}).get('message', '')[:70])
        if sid:
            st, r = call('/short-rent-orders/%s/confirm' % sid, 'POST', {}, admin)
            step('旅程9', '订单确认', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/short-rent-orders/%s/pay' % sid, 'POST', {'amount': 520}, admin)
            step('旅程9', '订单收款', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/short-rent-orders/%s/check-in' % sid, 'POST', {}, admin)
            step('旅程9', '办理入住', st == 200, (r or {}).get('message', '')[:60])
            st, r = call('/short-rent-orders/%s/check-out' % sid, 'POST',
                         {'extraAmount': 0}, admin)
            step('旅程9', '办理退房', st == 200, (r or {}).get('message', '')[:60])

    # ------------------------------------------------------------ 旅程10
    print('\n[旅程10] 欠费催缴：扫描逾期 → 生成催缴动作 → 动作可查')
    st, r = call('/fin/arrears/scan', 'GET', None, admin)
    step('旅程10', '逾期扫描可执行', st == 200, (r or {}).get('message', '')[:60])

    st, rb = call('/fin/bills?pageNum=1&pageSize=50&billStatus=OVERDUE', 'GET', None, admin)
    overdue = [x for x in rows((st, rb))
               if x.get('contractId') and x.get('personId')
               and float(x.get('payableAmount') or 0) > 0]
    step('旅程10', '存在可催缴的逾期账单', st == 200, '共 %d 条' % len(overdue))

    if overdue:
        b = overdue[0]
        st, ra = call('/fin/arrears', 'POST', {
            'contractId': b.get('contractId'), 'personId': b.get('personId'),
            'actionType': 'NOTIFY', 'triggerType': 'MANUAL',
            'arrearsAmount': b.get('payableAmount') or 100,
            'remark': '闭环测试催缴'}, admin)
        act = data((st, ra)) or {}
        step('旅程10', '登记催缴动作', st in (200, 400), (ra or {}).get('message', '')[:70])
        st, rl = call('/fin/arrears?pageNum=1&pageSize=5', 'GET', None, admin)
        step('旅程10', '催缴记录可查', st == 200 and len(rows((st, rl))) > 0,
             '共 %d 条' % len(rows((st, rl))))
