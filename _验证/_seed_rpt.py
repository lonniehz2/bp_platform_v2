# -*- coding: utf-8 -*-
"""补种报表定义 + 大屏定义（verify.py 清表后必需），并直接验证接口"""
import json
import urllib.request

import pymysql

NOW = '2026-10-20 13:00:00'
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()

# ---------- 1) 报表定义 ----------
cur.execute("DELETE FROM bp_rpt_report_def WHERE tenant_id IS NULL")
REPORTS = [('HOUSE_LEDGER', '房源台账', 'HOUSE'),
           ('CONTRACT_LEDGER', '合同台账', 'CONTRACT'),
           ('ARREARS_LEDGER', '欠费台账', 'FINANCE')]
for i, (code, name, typ) in enumerate(REPORTS, 1):
    cur.execute("""INSERT INTO bp_rpt_report_def
        (id, tenant_id, report_code, report_name, report_type, export_format,
         report_status, is_deleted, create_time, update_time)
        VALUES (%s,NULL,%s,%s,%s,'CSV','ENABLED',0,%s,%s)""",
                (770000000000000000 + i * 100, code, name, typ, NOW, NOW))
print('报表定义 %d 条' % len(REPORTS))

# ---------- 2) 大屏定义 ----------
cur.execute("DELETE FROM bp_rpt_screen_def WHERE tenant_id IS NULL")
WIDGETS = json.dumps([
    {"code": "HOUSE_TOTAL", "title": "房源总数", "chart": "NUMBER"},
    {"code": "OCCUPANCY_RATE", "title": "出租率", "chart": "GAUGE"},
    {"code": "HOUSE_VACANT", "title": "空置房源", "chart": "NUMBER"},
    {"code": "BILL_UNPAID_COUNT", "title": "欠费账单", "chart": "NUMBER"},
    {"code": "BILL_UNPAID_AMOUNT", "title": "欠费金额", "chart": "NUMBER"},
    {"code": "PAYMENT_TOTAL_AMOUNT", "title": "累计收款", "chart": "NUMBER"},
    {"code": "ACCESS_TODAY_COUNT", "title": "今日开门", "chart": "NUMBER"},
    {"code": "ACCESS_ABNORMAL_COUNT", "title": "今日异常开门", "chart": "LINE"},
], ensure_ascii=False)
cur.execute("""INSERT INTO bp_rpt_screen_def
    (id, tenant_id, screen_code, screen_name, screen_type, widget_config,
     refresh_seconds, screen_status, is_deleted, create_time, update_time)
    VALUES (%s,NULL,'OVERVIEW','住房保障运营总览','OVERVIEW',%s,60,'ENABLED',0,%s,%s)""",
            (780000000000000001, WIDGETS, NOW, NOW))
print('大屏定义 1 条（OVERVIEW，8 组件）')

# ---------- 3) 大屏权限 ----------
cur.execute("DELETE FROM bp_iam_role_permission WHERE permission_id IN "
            "(SELECT id FROM bp_iam_permission WHERE perm_code='rpt:screen:edit')")
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code='rpt:screen:edit'")
cur.execute("""INSERT INTO bp_iam_permission
    (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
    VALUES (790000000000000020,NULL,'rpt:screen:edit','大屏配置','API',420,
            'ENABLED',%s)""", (NOW,))
cur.execute("""INSERT INTO bp_iam_role_permission
    (id, tenant_id, role_id, permission_id, create_time)
    VALUES (796000000000000020,'350600',710000000000000001,
            790000000000000020,%s)""", (NOW,))
c.commit()
print('大屏权限已授予管理员')
c.close()

# ---------- 4) 直接验证接口 ----------
BASE = 'http://192.168.31.11:8080'


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    with urllib.request.urlopen(r, timeout=20) as x:
        return json.loads(x.read().decode())


tok = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )['data']['token']

d = call('GET', '/api/v1/rpt/screens/OVERVIEW/data', tok=tok)
print('\n大屏接口：%s' % d.get('code'))
w = (d.get('data') or {}).get('widgets') or []
print('组件数：%d' % len(w))
for x in w:
    print('  %-22s %-8s = %s' % (x.get('title'), x.get('chart'), x.get('value')))

m2 = call('GET', '/api/v1/rpt/metrics/current', tok=tok)
print('\n指标接口：%s  共 %d 项'
      % (m2.get('code'), len(m2.get('data') or {})))
