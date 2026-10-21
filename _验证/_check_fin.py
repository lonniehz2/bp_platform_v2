# -*- coding: utf-8 -*-
"""状态检查 + 查看 fin 剩余三张表结构"""
import json
import urllib.error
import urllib.request

import pymysql

BASE = 'http://192.168.31.11:8080'
H = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600', 'X-User-Id': '1001'}


def call(m, p, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=20) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return -1, {'error': str(e)}


print('=== 应用状态 ===')
try:
    print('健康:', urllib.request.urlopen(BASE + '/actuator/health', timeout=10).read().decode())
except Exception as e:
    print('健康检查失败:', e)

st, r = call('GET', '/api/v1/short-rent-orders?pageNum=1&pageSize=1')
print('短租订单接口:', r.get('code') or r.get('error'))
st, r = call('GET', '/api/v1/fin/arrears/scan?minOverdueDays=1')
print('欠费扫描接口:', r.get('code') or r.get('error'))

print()
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bp_platform'")
print('总表数:', cur.fetchone()[0])
cur.execute("""SELECT COUNT(*) FROM information_schema.TABLES
               WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_biz_short_rent_order'""")
print('短租订单表存在:', cur.fetchone()[0] == 1)
print()

for t in ('bp_fin_dunning_record', 'bp_fin_reconcile', 'bp_fin_cash_flow'):
    cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s
                   ORDER BY ORDINAL_POSITION""", (t,))
    rows = cur.fetchall()
    print('=== %s (%d 列) ===' % (t, len(rows)))
    for n, ty, nul, cm in rows:
        print('  %-24s %-15s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:56]))
    print()
c.close()
