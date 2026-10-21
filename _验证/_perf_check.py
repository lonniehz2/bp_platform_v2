# -*- coding: utf-8 -*-
"""压测后服务端体检：CPU/内存/连接数 + 慢查询索引检查"""
import subprocess
import sys

import pymysql

CMD = (
    "echo '--- LOAD ---'; cat /proc/loadavg; "
    "echo '--- CPU ---'; top -bn1 | head -5 | tail -3; "
    "echo '--- MEM ---'; free -m | head -2; "
    "echo '--- JAVA ---'; ps -o rss=,pcpu= -C java | awk '{print \"rss_kb=\"$1, \"cpu%=\"$2}'; "
    "echo '--- CONN ---'; ss -tn state established '( sport = :8080 )' | wc -l; "
    "echo '--- ERR ---'; grep -c 'URLError\\|Connection refused\\|HikariPool' "
    "/var/log/bp-platform/app.log 2>/dev/null || echo 0"
)
p = subprocess.run([sys.executable, 'vm.py', CMD], capture_output=True, text=True,
                   encoding='utf-8', errors='replace',
                   cwd=r'D:\Work\业务平台开发\_验证')
print('=== 服务端资源 ===')
print(p.stdout.strip()[:1600])

print()
print('=== 关键查询索引检查 ===')
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
checks = [
    ("账单按状态汇总（指标核心）",
     "EXPLAIN SELECT SUM(payable_amount) FROM bp_fin_bill "
     "WHERE bill_status IN ('UNPAID','PARTIAL','OVERDUE') AND tenant_id='350600'"),
    ("收款按状态汇总",
     "EXPLAIN SELECT SUM(pay_amount) FROM bp_fin_payment "
     "WHERE pay_status='SUCCESS' AND tenant_id='350600'"),
    ("房屋按状态计数",
     "EXPLAIN SELECT COUNT(*) FROM bp_asset_house "
     "WHERE house_status IN ('OCCUPIED','ALLOCATED') AND tenant_id='350600'"),
    ("开门记录按时间",
     "EXPLAIN SELECT COUNT(*) FROM bp_dev_access_record "
     "WHERE open_time >= '2026-10-19 00:00:00' AND tenant_id='350600'"),
]
for name, sql in checks:
    cur.execute(sql)
    rows = cur.fetchall()
    for r in rows:
        table = r[2] if len(r) > 2 else '?'
        typ = r[4] if len(r) > 4 else '?'
        key = r[6] if len(r) > 6 else '?'
        rowsx = r[9] if len(r) > 9 else '?'
        extra = r[11] if len(r) > 11 else ''
        print('  %-24s table=%-22s type=%-8s key=%-28s rows=%-6s %s'
              % (name, table, typ, key, rowsx, str(extra)[:40]))
        break
print()
for t in ('bp_fin_bill', 'bp_fin_payment', 'bp_asset_house', 'bp_dev_access_record'):
    cur.execute("SELECT COUNT(*) FROM %s" % t)
    print('  %-24s 行数 %s' % (t, cur.fetchone()[0]))
c.close()
