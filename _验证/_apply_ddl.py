# -*- coding: utf-8 -*-
"""建 bp_sys_file 表 + 校验现有表结构"""
import io

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()

# 1) 建附件表
ddl = io.open(r'D:\Work\业务平台开发\_验证\_ddl_sys_file.sql', encoding='utf-8').read()
for stmt in [s.strip() for s in ddl.split(';') if s.strip() and not s.strip().startswith('--')]:
    cur.execute(stmt)
c.commit()
cur.execute("SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_sys_file'")
print('  bp_sys_file 已建：%s' % ('是' if cur.fetchone()[0] else '否'))

# 2) 核对本轮新增的表是否都在
NEW_TABLES = ['bp_sys_file', 'bp_sys_dict', 'bp_sys_config', 'bp_sys_audit_log',
              'bp_msg_template', 'bp_msg_send_record', 'bp_msg_todo',
              'bp_msg_subscription', 'bp_rpt_report_def', 'bp_rpt_export_task',
              'bp_rpt_metric_daily', 'bp_rpt_screen_def',
              'bp_dev_access_record', 'bp_grant_audit_log', 'bp_grant_keyring',
              'bp_grant_reconcile_diff', 'bp_grant_iot_person_map',
              'bp_open_app', 'bp_open_api', 'bp_open_call_log', 'bp_open_webhook',
              'bp_open_webhook_log', 'bp_gov_adapter_config', 'bp_gov_adapter_log',
              'bp_gov_report_task', 'bp_gov_report_detail',
              'bp_rule_ruleset', 'bp_rule_rule', 'bp_rule_execute_log',
              'bp_ops_alert_rule', 'bp_person_guarantee_profile',
              'bp_person_verify_record']
miss = []
for t in NEW_TABLES:
    cur.execute("SELECT COUNT(*) FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s", (t,))
    if not cur.fetchone()[0]:
        miss.append(t)
print('  本轮相关表 %d 张，缺失 %d 张%s'
      % (len(NEW_TABLES), len(miss), ('：' + ', '.join(miss)) if miss else ''))

cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bp_platform'")
print('  库内表总数：%d' % cur.fetchone()[0])
c.close()
