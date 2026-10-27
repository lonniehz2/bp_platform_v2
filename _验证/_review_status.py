# -*- coding: utf-8 -*-
"""四级审批现状盘点。"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()

print('--- 申请状态 ---')
cur.execute('select application_status, count(*) from bp_biz_application group by application_status')
for r in cur.fetchall():
    print('  ', r)

print('--- 当前环节 ---')
cur.execute('select current_node, count(*) from bp_biz_application group by current_node')
for r in cur.fetchall():
    print('  ', r)

print('--- 审核记录 阶段/结果 ---')
cur.execute('select review_stage, review_result, count(*) from bp_biz_review_record '
            'group by review_stage, review_result')
for r in cur.fetchall():
    print('  ', r)

print('--- 走满 4 阶段的申请数 ---')
cur.execute('select count(*) from (select application_id, count(distinct review_stage) s '
            'from bp_biz_review_record group by application_id having s >= 4) t')
print('  ', cur.fetchone())

print('--- 联审部门分布 ---')
cur.execute('select ifnull(review_dept,"(空)"), count(*) from bp_biz_review_record '
            'group by review_dept order by 2 desc limit 6')
for r in cur.fetchall():
    print('  ', r)

print('--- 审核方式 ---')
cur.execute('select review_type, count(*) from bp_biz_review_record group by review_type')
for r in cur.fetchall():
    print('  ', r)

c.close()
