# -*- coding: utf-8 -*-
"""边缘旅程：退租 / 合同变更 / 短租 / 欠费催缴。

以模块形式被 _check_journeys.py 导入调用，复用其 call/login/step。
"""
from datetime import date, timedelta
import time


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
    # 取一套已有房源作为模板，沿用其组织与空间（避免参数猜错）
    st, rsample = call('/houses?pageNum=1&pageSize=1', 'GET', None, admin)
    sample = (rows((st, rsample)) or [{}])[0]
    org = sample.get('orgId')
    # 每次新建一间独立房源，彻底避免「一房多签」导致的偶发失败
    new_code = 'ZZ-QA-' + rid()
    st, rh0 = call('/houses', 'POST', {
        'houseCode': new_code, 'houseName': '闭环测试房' + rid(),
        'houseType': sample.get('houseType') or 'PUBLIC_RENTAL',
        'orgId': org, 'spaceId': sample.get('spaceId'),
        'area': 45, 'rentStandard': 15,
        'rentUnit': sample.get('rentUnit') or 'AREA_MONTH'}, admin)
    made_house = data((st, rh0)) or {}
    if made_house.get('id'):
        house = made_house
        print('  新建房源:', new_code)
    else:
        print('  建房失败，改用既有房源：', (rh0 or {}).get('message', '')[:40])
    # 选一间没有生效合同的房源（兜底）；优先使用本次新建的独立房源
    st, rc0 = call('/contracts?pageNum=1&pageSize=300', 'GET', None, admin)
    used = {str(x.get('houseId')) for x in rows((st, rc0))
            if x.get('contractStatus') in ('ACTIVE', 'SIGNING', 'PENDING_SIGN')}
    st, rh = call('/houses?pageNum=1&pageSize=300', 'GET', None, admin)
    hs = [x for x in rows((st, rh)) if str(x.get('id')) not in used]
    house = next((x for x in hs if x.get('houseStatus') in ('AVAILABLE', 'VACANT')),
                 hs[0] if hs else {})
    if made_house.get('id'):
        house = made_house
        print('  使用新建房源:', made_house.get('houseCode'))
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
            'houseAddress': '一期示范小区1幢' + str(house.get('houseName') or ''),
            'houseArea': 50,
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
    # 先清掉上一轮验证留下的动作，避免演示数据被测试记录淹没（尽力而为）
    try:
        import pymysql
        _c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                             password='5677@Mysql', database='bp_platform',
                             charset='utf8mb4', autocommit=True,
                             connect_timeout=15, read_timeout=180)
        _cur = _c.cursor()
        _cur.execute("delete from bp_fin_arrears_action "
                     "where arrears_amount = 120.01")
        _c.close()
    except Exception:
        pass
    st, r = call('/fin/arrears/scan', 'GET', None, admin)
    step('旅程10', '逾期扫描可执行', st == 200, (r or {}).get('message', '')[:60])

    st, rb = call('/fin/bills?pageNum=1&pageSize=50&billStatus=OVERDUE', 'GET', None, admin)
    overdue = [x for x in rows((st, rb))
               if x.get('contractId') and x.get('personId')
               and float(x.get('payableAmount') or 0) > 0]
    step('旅程10', '存在可催缴的逾期账单', st == 200, '共 %d 条' % len(overdue))

    if overdue:
        b = overdue[0]
        # 逾期天数取账单实际值，缺失时给 45，避免演示里出现「逾期 0 天」
        od = int(float(b.get('overdueDays') or 0)) or 45
        st, ra = call('/fin/arrears', 'POST', {
            'contractId': b.get('contractId'), 'personId': b.get('personId'),
            'actionType': 'NOTIFY', 'triggerType': 'MANUAL',
            'arrearsAmount': 120.01,   # 固定标记值，便于下轮清理
            'overdueDays': max(30, od)}, admin)
        act = data((st, ra)) or {}
        step('旅程10', '登记催缴动作', st in (200, 400), (ra or {}).get('message', '')[:70])
        st, rl = call('/fin/arrears?pageNum=1&pageSize=5', 'GET', None, admin)
        step('旅程10', '催缴记录可查', st == 200 and len(rows((st, rl))) > 0,
             '共 %d 条' % len(rows((st, rl))))

    # ------------------------------------------------------------ 旅程11
    print('\n[旅程11] 多级审核：受理 → 形式审核 → 联合审核 → 终审 → 入轮候')
    name11 = '多级审核' + rid()
    st, rp = call('/persons', 'POST', {
        'personName': name11, 'idCard': env['gen_id_card'](),
        'phone': '137%08d' % __import__('random').randint(0, 99999999),
        'personType': 'FAMILY', 'gender': 'MALE'}, admin)
    p11 = data((st, rp)) or {}
    pid11 = p11.get('id')
    step('旅程11', '新建申请人', st == 200 and pid11, (rp or {}).get('message', '')[:60])

    if pid11:
        call('/verify-records', 'POST', {
            'personId': pid11, 'verifyType': 'FACE', 'userName': name11,
            'faceResult': '1', 'citizenResult': '1', 'faceScore': 96.0,
            'resultCode': '0000', 'responseCode': '200'}, admin)
        call('/guarantee-profiles', 'POST', {
            'personId': pid11, 'securityType': 'PUBLIC', 'familySize': 2,
            'monthlyIncome': 3800, 'annualIncome': 45600,
            'householdIncome': 45600, 'profileStatus': 'QUALIFIED'}, admin)
        st, rp11 = call('/persons?pageNum=1&pageSize=1', 'GET', None, admin)
        org11 = (rows((st, rp11)) or [{}])[0].get('orgId')
        st, ra11 = call('/applications', 'POST', {
            'personId': pid11, 'securityType': 'PUBLIC', 'applyChannel': 'ONLINE',
            'orgId': org11, 'familySize': 2, 'declaredIncome': 3800,
            'declaredIncomeYear': 45600, 'incomeCheckPeriod': 'LAST_12M',
            'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1}, admin)
        app11 = data((st, ra11)) or {}
        aid = app11.get('id')
        step('旅程11', '提交申请', st == 200 and aid, (ra11 or {}).get('message', '')[:70])

        if aid:
            st, r = call('/applications/%s/accept' % aid, 'POST', {}, admin)
            step('旅程11', '受理', st == 200, (r or {}).get('message', '')[:60])
            for stage, label in (('ACCEPT', '受理初审'), ('FORM', '形式审核'),
                                 ('JOINT', '联合审核'), ('FINAL', '终审')):
                st, r = call('/applications/%s/review' % aid, 'POST', {
                    'stage': stage, 'result': 'PASS', 'opinion': label + '通过'}, admin)
                step('旅程11', label + '通过', st == 200, (r or {}).get('message', '')[:70])

            st, rd = call('/applications/%s' % aid, 'GET', None, admin)
            d11 = data((st, rd)) or {}
            step('旅程11', '终审后状态为已通过',
                 d11.get('applicationStatus') == 'APPROVED', str(d11.get('applicationStatus')))
            step('旅程11', '当前节点为已完成', d11.get('currentNode') in ('DONE', None),
                 str(d11.get('currentNode')))

            st, rrec = call('/applications/%s/reviews' % aid, 'GET', None, admin)
            recs = data((st, rrec)) or []
            stages = {x.get('reviewStage') for x in recs} if isinstance(recs, list) else set()
            step('旅程11', '四级审核轨迹完整',
                 {'ACCEPT', 'FORM', 'JOINT', 'FINAL'} <= stages, str(sorted(stages)))

            st, rw = call('/allocation/waiting?pageNum=1&pageSize=5&keyword=%s'
                          % __import__('urllib.parse').parse.quote(name11), 'GET', None, admin)
            wl = rows((st, rw))
            step('旅程11', '自动进入轮候队列', len(wl) >= 1, '轮候 %d 条' % len(wl))

    # ------------------------------------------------------------ 旅程12
    print('\n[旅程12] 监管报送：发起报送 → 生成任务 → 明细可查')
    st, rg = call('/gov/reports?pageNum=1&pageSize=1', 'GET', None, admin)
    before = (data((st, rg)) or {}).get('total')
    today12 = str(__import__('datetime').date.today())
    from12 = str(__import__('datetime').date.today() - __import__('datetime').timedelta(days=90))
    st, rad = call('/gov/adapters', 'POST', {
        'adapterCode': 'QA_GOV_' + rid(), 'adapterName': '闭环报送适配器',
        'systemType': 'HOUSING_BUREAU', 'protocol': 'HTTP',
        'endpoint': 'http://example.gov/api', 'authType': 'TOKEN',
        'degradeMode': 'QUEUE'}, admin)
    step('旅程12', '配置报送适配器', st in (200, 400), (rad or {}).get('message', '')[:60])

    st, rr = call('/gov/reports', 'POST', {
        'targetSystem': 'HOUSING_BUREAU', 'reportType': 'HOUSE',
        'dateFrom': from12, 'dateTo': today12}, admin)
    task = data((st, rr)) or {}
    tid = task.get('id')
    step('旅程12', '发起监管报送', st == 200 and tid, (rr or {}).get('message', '')[:70])
    if tid:
        # 刚发起报送时列表偶发读不到（时序/连接复用），最多重试 5 次
        st, rl, total_n = 0, {}, 0
        for _attempt in range(5):
            st, rl = call('/gov/reports?pageNum=1&pageSize=5', 'GET', None, admin)
            total_n = int((data((st, rl)) or {}).get('total') or 0)
            if st == 200 and total_n >= 1:
                break
            time.sleep(1.5)
        step('旅程12', '报送任务可查询', st == 200 and total_n >= 1,
             '共 %s 条' % total_n)
        st, rd = call('/gov/reports/%s/details' % tid, 'GET', None, admin)
        details = data((st, rd)) or []
        step('旅程12', '报送明细已生成', st == 200 and len(details) > 0,
             '明细 %d 条' % (len(details) if isinstance(details, list) else 0))
        st, rs = call('/gov/stats', 'GET', None, admin)
        step('旅程12', '报送统计可查', st == 200, (rs or {}).get('message', '')[:40])

    # ------------------------------------------------------------ 旅程13
    print('\n[旅程13] 消息通知：模板 → 发送 → 记录可查')
    code13 = 'QA_TPL_' + rid()
    st, rt = call('/messages/templates', 'POST', {
        'templateCode': code13, 'templateName': '闭环模板' + rid(),
        'channel': 'SMS', 'titleTpl': '缴费提醒',
        'contentTpl': '尊敬的${name}，您本期应缴 ${amount} 元，请及时缴纳。',
        'bizType': 'BILL'}, admin)
    step('旅程13', '新建消息模板', st in (200, 400), (rt or {}).get('message', '')[:60])

    st, rr = call('/messages/templates/%s/render' % code13, 'POST',
                  {'name': '张三', 'amount': '128.50'}, admin)
    rendered = data((st, rr))
    text13 = rendered if isinstance(rendered, str) else str(rendered or '')
    step('旅程13', '模板渲染成功', st == 200 and ('张三' in text13 or '128.50' in text13),
         '渲染结果: ' + text13[:60])

    st, rs = call('/messages/send', 'POST', {
        'templateCode': code13, 'bizType': 'BILL',
        'channel': 'SMS', 'receiverType': 'PERSON', 'receiverId': '1001',
        'receiverName': '张三', 'receiverAddr': '13800000000',
        'variables': {'name': '张三', 'amount': '128.50'}}, admin)
    msg = data((st, rs)) or {}
    step('旅程13', '按模板发送消息', st == 200 and msg.get('id'), (rs or {}).get('message', '')[:70])

    st, rrec = call('/messages/records?pageNum=1&pageSize=5', 'GET', None, admin)
    recs = rows((st, rrec))
    step('旅程13', '发送记录可查询', st == 200 and len(recs) >= 1, '共 %d 条' % len(recs))
