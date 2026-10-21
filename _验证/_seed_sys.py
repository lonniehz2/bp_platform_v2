# -*- coding: utf-8 -*-
"""初始化字典与政策参数 + 补充审计/字典/参数权限"""
import pymysql

TENANT = '350600'
NOW = '2026-10-19 12:00:00'

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()

# ---------- 1) 字典（系统内置，tenant_id 为空） ----------
cur.execute("DELETE FROM bp_sys_dict WHERE dict_type IN "
            "('SECURITY_TYPE','HOUSE_TYPE','TERMINATION_TYPE','VIOLATION_TYPE',"
            "'SANCTION_TYPE','APPEAL_BIZ_TYPE')")
DICTS = [
    ('SECURITY_TYPE', 'PUBLIC', '公租房', 'PUBLIC', 1),
    ('SECURITY_TYPE', 'AFFORDABLE', '保障性租赁住房', 'AFFORDABLE', 2),
    ('SECURITY_TYPE', 'TALENT', '人才公寓', 'TALENT', 3),
    ('SECURITY_TYPE', 'LOW_RENT', '廉租住房', 'LOW_RENT', 4),
    ('HOUSE_TYPE', 'PUBLIC_RENTAL', '公租房', 'PUBLIC_RENTAL', 1),
    ('HOUSE_TYPE', 'APARTMENT', '公寓', 'APARTMENT', 2),
    ('HOUSE_TYPE', 'DORMITORY', '宿舍', 'DORMITORY', 3),
    ('HOUSE_TYPE', 'HOTEL', '酒店/民宿', 'HOTEL', 4),
    ('TERMINATION_TYPE', 'NORMAL', '正常退租', 'NORMAL', 1),
    ('TERMINATION_TYPE', 'EXPEL', '违规清退', 'EXPEL', 2),
    ('TERMINATION_TYPE', 'EXPIRE', '到期不续', 'EXPIRE', 3),
    ('TERMINATION_TYPE', 'EXCHANGE', '换房退出', 'EXCHANGE', 4),
    ('VIOLATION_TYPE', 'FALSE_INFO', '提供虚假信息', 'FALSE_INFO', 1),
    ('VIOLATION_TYPE', 'SUBLEASE', '转租出借', 'SUBLEASE', 2),
    ('VIOLATION_TYPE', 'ARREARS', '恶意欠租', 'ARREARS', 3),
    ('VIOLATION_TYPE', 'VACANT', '长期空置', 'VACANT', 4),
    ('SANCTION_TYPE', 'BAN_APPLY', '限制申请', 'BAN_APPLY', 1),
    ('SANCTION_TYPE', 'TERMINATE', '终止资格', 'TERMINATE', 2),
    ('SANCTION_TYPE', 'CREDIT_PLATFORM', '推送信用平台', 'CREDIT_PLATFORM', 3),
    ('APPEAL_BIZ_TYPE', 'ANNUAL_REVIEW', '年度核查', 'ANNUAL_REVIEW', 1),
    ('APPEAL_BIZ_TYPE', 'EXIT', '退出决定', 'EXIT', 2),
    ('APPEAL_BIZ_TYPE', 'PUBLICITY', '公示异议', 'PUBLICITY', 3),
]
for i, (t, code, label, val, sort) in enumerate(DICTS, start=1):
    cur.execute("""INSERT INTO bp_sys_dict
        (id, tenant_id, dict_type, dict_code, dict_label, dict_value, sort_no,
         is_default, dict_status, is_deleted, create_time, update_time)
        VALUES (%s,NULL,%s,%s,%s,%s,%s,0,'ENABLED',0,%s,%s)""",
                (750000000000000000 + i, t, code, label, val, sort, NOW, NOW))

# ---------- 2) 政策参数（全局，tenant_id 为空） ----------
cur.execute("DELETE FROM bp_sys_config WHERE config_key LIKE 'biz.%'")
CONFIGS = [
    ('biz.publicity.allocation.minDays', '7', 'INT', 'BUSINESS',
     '配租公示最短自然日（含首尾）'),
    ('biz.publicity.qualify.minDays', '5', 'INT', 'BUSINESS', '资格公示最短自然日'),
    ('biz.credit.banYears.severe', '5', 'INT', 'BUSINESS',
     '严重违规限制申请年限（转租/虚假信息/违法/破坏结构）'),
    ('biz.credit.banYears.normal', '1', 'INT', 'BUSINESS', '一般违规限制申请年限'),
    ('biz.termination.transition.months', '3', 'INT', 'BUSINESS',
     '腾退过渡期月数（重庆政策）'),
    ('biz.termination.transition.multiplier', '1.5', 'DECIMAL', 'BUSINESS',
     '过渡期租金倍率（重庆政策）'),
    ('biz.termination.relocation.maxMonths', '6', 'INT', 'BUSINESS',
     '搬迁期最大月数（成都政策）'),
    ('biz.exchange.maxTimes', '1', 'INT', 'BUSINESS', '同一租期最大换房次数（成都政策）'),
    ('biz.exchange.noExchange.multiplier', '1.5', 'DECIMAL', 'BUSINESS',
     '应换不换加价倍率（重庆政策）'),
    ('biz.allocation.lockHours', '72', 'INT', 'BUSINESS', '配租房源冻定时长（小时）'),
    ('biz.appeal.deadlineDays', '10', 'INT', 'BUSINESS', '申诉期限自然日'),
    ('biz.review.overdue.days', '0', 'INT', 'BUSINESS', '年审逾期阈值天数'),
]
for i, (k, v, vt, grp, desc) in enumerate(CONFIGS, start=1):
    cur.execute("""INSERT INTO bp_sys_config
        (id, tenant_id, config_key, config_value, config_group, value_type,
         is_encrypted, is_system, description, create_time, update_time)
        VALUES (%s,NULL,%s,%s,%s,%s,0,1,%s,%s,%s)""",
                (760000000000000000 + i, k, v, grp, vt, desc, NOW, NOW))

# ---------- 3) 补充 sys 权限并授予管理员角色 ----------
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code LIKE 'sys:%'")
SYS_PERMS = [
    ('sys:audit:list', '审计日志查询'),
    ('sys:dict:edit', '字典维护'),
    ('sys:config:list', '参数查询'),
    ('sys:config:edit', '参数维护'),
]
for i, (code, name) in enumerate(SYS_PERMS, start=1):
    pid = 770000000000000000 + i
    cur.execute("""INSERT INTO bp_iam_permission
        (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
        VALUES (%s,NULL,%s,%s,'API',%s,'ENABLED',%s)""",
                (pid, code, name, 100 + i, NOW))
    cur.execute("""INSERT INTO bp_iam_role_permission
        (id, tenant_id, role_id, permission_id, create_time)
        VALUES (%s,%s,710000000000000001,%s,%s)""",
                (780000000000000000 + i, TENANT, pid, NOW))

c.commit()

cur.execute("SELECT COUNT(*) FROM bp_sys_dict")
d = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_sys_config")
cfg = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_iam_permission WHERE perm_code LIKE 'sys:%'")
sp = cur.fetchone()[0]
print('初始化完成：字典 %d 条，政策参数 %d 条，sys 权限 %d 条' % (d, cfg, sp))
print()
print('政策参数：')
for k, v, vt, grp, desc in CONFIGS:
    print('  %-46s = %-6s  %s' % (k, v, desc[:30]))
c.close()
