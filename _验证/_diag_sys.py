# -*- coding: utf-8 -*-
"""排查：租户忽略表清单 + sys 表实际数据"""
import io
import re

import pymysql

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\config\MybatisTenantConfig.java')
s = io.open(p, encoding='utf-8').read()
print('=== MybatisTenantConfig 忽略表配置 ===')
for m in re.finditer(r'(IGNORE|ignore|ignoreTable|Table)\w*\s*=?\s*\(?([^;]{0,400})', s):
    txt = m.group(0).strip()
    if 'bp_' in txt:
        print('  ' + txt[:400])
print()
print('=== 含 bp_ 的行 ===')
for ln in s.split('\n'):
    if 'bp_' in ln:
        print('  ' + ln.strip()[:160])
print()

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
for t in ('bp_sys_config', 'bp_sys_dict', 'bp_sys_audit_log'):
    cur.execute("SELECT COUNT(*) FROM %s" % t)
    print('%s 行数：%d' % (t, cur.fetchone()[0]))
cur.execute("SELECT config_key, config_value, IFNULL(tenant_id,'NULL') FROM bp_sys_config LIMIT 4")
print()
print('config 样例：')
for r in cur.fetchall():
    print('  %-46s %-6s tenant=%s' % r)
cur.execute("SELECT COUNT(*) FROM bp_sys_config WHERE tenant_id IS NULL")
print('全局(tenant_id IS NULL) 参数：%d' % cur.fetchone()[0])
cur.execute("SELECT audit_type, audit_level, action, IFNULL(operator_name,'-') "
            "FROM bp_sys_audit_log ORDER BY id DESC LIMIT 5")
print()
print('审计样例：')
rows = cur.fetchall()
if not rows:
    print('  （无审计记录）')
for r in rows:
    print('  %-10s %-10s %-20s %s' % r)
c.close()
