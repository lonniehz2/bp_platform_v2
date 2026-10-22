# -*- coding: utf-8 -*-
"""盘点当前库内业务数据，识别测试残留命名。"""
import pymysql

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()

TABLES = [
    ('bp_iam_org', '组织'),
    ('bp_asset_house', '房源'),
    ('bp_asset_space', '空间'),
    ('bp_person_person', '人员'),
    ('bp_person_guarantee_profile', '保障档案'),
    ('bp_biz_application', '申请'),
    ('bp_biz_waiting', '轮候'),
    ('bp_biz_batch', '配租批次'),
    ('bp_biz_lottery_result', '摇号结果'),
    ('bp_biz_publicity', '公示'),
    ('bp_biz_contract', '合同'),
    ('bp_fin_bill', '账单'),
    ('bp_fin_payment', '收款'),
    ('bp_fin_deposit', '押金'),
    ('bp_biz_termination', '退租单'),
]
print('%-28s %-6s %s' % ('表', '总数', '样例'))
for t, label in TABLES:
    try:
        cur.execute('select count(*) from %s' % t)
        n = cur.fetchone()[0]
        sample = ''
        if n:
            col = 'org_name' if t == 'bp_iam_org' else (
                'house_name' if t == 'bp_asset_house' else (
                    'real_name' if 'person' in t and 'profile' not in t else (
                        'contract_no' if t == 'bp_biz_contract' else (
                            'batch_name' if t == 'bp_biz_batch' else (
                                'title' if t == 'bp_biz_publicity' else 'id')))))
            cur.execute('select %s from %s limit 3' % (col, t))
            sample = ' | '.join(str(r[0]) for r in cur.fetchall())
        print('%-28s %-6s %s' % (t, n, sample))
    except Exception as ex:
        print('%-28s 查询失败 %s' % (t, ex))

# 残留识别
print('\n--- 测试残留 ---')
for t, col, pat in [
    ('bp_person_person', 'real_name', '实测%'),
    ('bp_person_person', 'real_name', '测试%'),
    ('bp_iam_org', 'org_name', '测试%'),
    ('bp_iam_org', 'org_name', '演示%'),
    ('bp_iam_user', 'username', 'wtest%'),
    ('bp_iam_user', 'username', 'test_%'),
    ('bp_biz_batch', 'batch_name', '联调%'),
    ('bp_biz_publicity', 'title', '联动%'),
    ('bp_asset_house', 'house_name', '第0%'),
]:
    try:
        cur.execute('select count(*) from %s where %s like %%s' % (t, col), (pat,))
        print('%-22s %-12s %-10s %s' % (t, col, pat, cur.fetchone()[0]))
    except Exception as ex:
        print('%-22s %s 失败: %s' % (t, pat, ex))

conn.close()
