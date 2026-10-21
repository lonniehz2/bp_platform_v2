# -*- coding: utf-8 -*-
"""初始化消息模板（系统内置，tenant_id 为空）"""
import pymysql

NOW = '2026-10-19 12:00:00'
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
cur.execute("DELETE FROM bp_msg_template WHERE tenant_id IS NULL")

TPL = [
    ('BILL_DUE', '账单到期提醒', 'SMS', 'BILL_DUE',
     '【住房保障】缴费提醒',
     '尊敬的${name}：您${period}的${feeName}账单应缴${amount}元，'
     '请于${dueDate}前缴纳，逾期将产生滞纳金。'),
    ('ARREARS', '欠费催缴', 'SMS', 'ARREARS',
     '【住房保障】欠费催缴通知',
     '尊敬的${name}：您已欠缴${amount}元，逾期${days}天。'
     '请尽快缴纳，避免影响您的保障资格。'),
    ('CONTRACT_EXPIRE', '合同到期提醒', 'INNER', 'CONTRACT_EXPIRE',
     '合同即将到期',
     '您的合同将于${leaseEnd}到期，如需续租请在到期前30日内提交申请。'),
    ('ANNUAL_REVIEW', '年审通知', 'INNER', 'ANNUAL_REVIEW',
     '年度资格复核通知',
     '请于${deadline}前提交${year}年度复核材料，逾期未复核将影响保障资格。'),
    ('ALLOCATION_WIN', '配租中签通知', 'INNER', 'ALLOCATION',
     '恭喜您中签',
     '您在${batchName}中签，房源${houseCode}，请于${signDeadline}前完成签约。'),
    ('APPEAL_RESULT', '申诉结果告知', 'INNER', 'APPEAL',
     '申诉处理结果',
     '您对${bizName}的申诉结果为：${result}。${opinion}'),
]
for i, (code, name, ch, biz, title, content) in enumerate(TPL, start=1):
    cur.execute("""INSERT INTO bp_msg_template
        (id, tenant_id, template_code, template_name, channel, biz_type, title_tpl,
         content_tpl, template_status, is_deleted, create_time, update_time)
        VALUES (%s,NULL,%s,%s,%s,%s,%s,%s,'ENABLED',0,%s,%s)""",
                (770000000000000000 + i * 10, code, name, ch, biz, title, content, NOW, NOW))

# 订阅示例：欠费事件给财务岗（角色 710000000000000005 为 VIEWER，改用 FINANCE=...04）
cur.execute("DELETE FROM bp_msg_subscription WHERE tenant_id='350600'")
SUBS = [
    ('ARREARS', 'ROLE', '710000000000000004', 'SMS,INNER'),
    ('CONTRACT_EXPIRE', 'ROLE', '710000000000000002', 'INNER'),
    ('ANNUAL_REVIEW', 'ROLE', '710000000000000003', 'INNER'),
]
for i, (biz, st, sid, chs) in enumerate(SUBS, start=1):
    cur.execute("""INSERT INTO bp_msg_subscription
        (id, tenant_id, biz_type, subscriber_type, subscriber_id, channels, sub_status,
         create_time, update_time)
        VALUES (%s,'350600',%s,%s,%s,%s,'ENABLED',%s,%s)""",
                (780000000000000000 + i, biz, st, sid, chs, NOW, NOW))

c.commit()
cur.execute("SELECT COUNT(*) FROM bp_msg_template WHERE tenant_id IS NULL")
t = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_msg_subscription WHERE tenant_id='350600'")
s = cur.fetchone()[0]
print('模板 %d 条，订阅 %d 条' % (t, s))
for code, name, ch, biz, title, content in TPL:
    print('  %-16s %-10s %-8s %s' % (code, ch, biz, name))
c.close()
