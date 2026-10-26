# -*- coding: utf-8 -*-
"""导入第五级行政区划（村/社区）到 bp_sys_region。

数据来源：China-Area-Region-Administrative-Divisions（国家统计局区划代码）
说明：省/市/区县/街道四级已存在（数量与数据集一致 31/342/3051/41274），
      本次只补第五级并回填街道的 has_child。
"""
import json
import io
import time

import pymysql

SRC = '_data/regions.json'
BATCH = 3000


def load_villages():
    data = json.load(io.open(SRC, encoding='utf-8'))
    rows = []
    streets_with_child = set()
    for prov in data:
        for city in prov.get('children') or []:
            for dist in city.get('children') or []:
                for street in dist.get('children') or []:
                    villages = street.get('children') or []
                    if villages:
                        streets_with_child.add(street['code'])
                    for v in villages:
                        rows.append((v['code'][:12], v['name'][:120],
                                     street['code'][:12], 5, 0))
    return rows, streets_with_child


def connect():
    return pymysql.connect(host='192.168.31.153', port=33306, user='root',
                           password='5677@Mysql', database='bp_platform',
                           charset='utf8mb4', autocommit=True,
                           connect_timeout=20, read_timeout=600, write_timeout=600)


rows, streets = load_villages()
print('待导入村/社区: %d 条；有下级的街道: %d 个' % (len(rows), len(streets)))

conn = connect()
cur = conn.cursor()
cur.execute("select count(*) from bp_sys_region where level=5")
print('导入前第五级:', cur.fetchone()[0])

t0 = time.time()
done = 0
for i in range(0, len(rows), BATCH):
    part = rows[i:i + BATCH]
    for attempt in range(3):
        try:
            cur.executemany(
                "insert ignore into bp_sys_region(code, name, parent_code, level, has_child) "
                "values (%s, %s, %s, %s, %s)", part)
            break
        except Exception as e:
            print('  批次重试 %d: %s' % (attempt + 1, str(e)[:60]))
            conn = connect()
            cur = conn.cursor()
    done += len(part)
    if done % 30000 == 0 or done == len(rows):
        print('  已写入 %d / %d（%.0fs）' % (done, len(rows), time.time() - t0))

# 回填街道 has_child
codes = list(streets)
for i in range(0, len(codes), 3000):
    part = codes[i:i + 3000]
    ph = ','.join(['%s'] * len(part))
    cur.execute("update bp_sys_region set has_child=1 where code in (%s)" % ph, part)

cur.execute("select level, count(*), sum(has_child) from bp_sys_region group by level order by level")
for r in cur.fetchall():
    print('  层级 %d：%d 条，其中 has_child=1 共 %s' % r)

cur.execute("select code,name,parent_code from bp_sys_region where parent_code='110101001000' order by code limit 5")
print('东华门街道下社区样例:', cur.fetchall())
conn.close()
print('完成，用时 %.1fs' % (time.time() - t0))
