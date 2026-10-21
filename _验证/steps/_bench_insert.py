# -*- coding: utf-8 -*-
# ===== 统一连接配置（由 _验证/verify.py 注入环境变量）=====
import os as _os
HOST  = _os.environ.get('BP_DB_HOST', '192.168.31.153')
PORT  = int(_os.environ.get('BP_DB_PORT', '33306'))
USER  = _os.environ.get('BP_DB_USER', 'root')
PWD   = _os.environ.get('BP_DB_PWD',  '5677@Mysql')
DB    = _os.environ.get('BP_DB_NAME', 'bp_platform')
BASE  = _os.environ.get('BP_PROJ_DIR', r'D:\Work\业务平台开发')
# =========================================================
"""
写入方法基准对比：找出真实可用的吞吐
列数 = 18（id..create_time），create_time 用 NOW(3) 由 SQL 补
"""
import pymysql, time


COLS = ('id,tenant_id,event_id,device_id,device_mac,space_id,house_id,org_id,open_type,'
        'open_type_name,is_trusted,person_id,target_user_mobile,open_time,source,'
        'is_abnormal,abnormal_type')
NPARAM = 17          # 上面共 17 列，create_time 由 NOW(3) 补齐
SQL_HEAD = "INSERT INTO bp_dev_access_record(%s,create_time) VALUES " % COLS

def connect():
    return pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                           charset='utf8mb4', connect_timeout=10, read_timeout=600)

def mkrow(base, i):
    return (base + i, '350600', 'BENCH%09d' % ((base + i) % 1000000000), 'LK00000001',
            'FF00FFE00001', 0, 0, 0, '1049', '人脸开门', 1, None, '13800000000',
            '2026-10-15 10:00:00', 'CALLBACK', 0, None)

PH = '(' + ','.join(['%s'] * NPARAM) + ',NOW(3))'

print('=== 基准 1：executemany（PyMySQL 逐行 INSERT）===')
c = connect(); cur = c.cursor()
base = 9100000000000000000
rows = [mkrow(base, i) for i in range(200)]
t0 = time.time(); cur.executemany(SQL_HEAD + PH, rows); c.commit()
dt = time.time() - t0
print('  200 行 耗时 %.2f s -> %.0f 行/秒' % (dt, 200 / dt if dt else 0))
cur.execute("DELETE FROM bp_dev_access_record WHERE id > %s" % base); c.commit(); c.close()

print('\n=== 基准 2：手拼多值 INSERT ===')
for size in (500, 2000):
    c = connect(); cur = c.cursor()
    base = 9200000000000000000 + size * 1000
    rows = [mkrow(base, i) for i in range(size)]
    stmt = SQL_HEAD + ','.join([PH] * size)
    flat = [v for r in rows for v in r]
    t0 = time.time(); cur.execute(stmt, flat); c.commit()
    dt = time.time() - t0
    print('  多值 %-5d 行 耗时 %6.3f s -> %7.0f 行/秒' % (size, dt, size / dt if dt else 0))
    cur.execute("DELETE FROM bp_dev_access_record WHERE id > %s" % base); c.commit(); c.close()

print('\n=== 基准 3：多值 10000 行 ===')
c = connect(); cur = c.cursor()
size = 10000; base = 9300000000000000000
rows = [mkrow(base, i) for i in range(size)]
stmt = SQL_HEAD + ','.join([PH] * size)
flat = [v for r in rows for v in r]
t0 = time.time(); cur.execute(stmt, flat); c.commit()
dt = time.time() - t0
print('  多值 %-5d 行 耗时 %6.3f s -> %7.0f 行/秒' % (size, dt, size / dt if dt else 0))
cur.execute("DELETE FROM bp_dev_access_record WHERE id > %s" % base); c.commit()

print('\n=== 基准 4：多值 10000 × 5 批，仅 1 次提交 ===')
size_each, batches = 10000, 5
base = 9400000000000000000
stmt = SQL_HEAD + ','.join([PH] * size_each)
t0 = time.time(); done = 0
for b in range(batches):
    rows = [mkrow(base + b * size_each, i) for i in range(size_each)]
    flat = [v for r in rows for v in r]
    cur.execute(stmt, flat)
    done += size_each
c.commit()
dt = time.time() - t0
print('  %d 行（仅 1 次提交）耗时 %.3f s -> %.0f 行/秒' % (done, dt, done / dt if dt else 0))
cur.execute("DELETE FROM bp_dev_access_record WHERE id >= %s" % base); c.commit()

cur.execute("SELECT COUNT(*) FROM bp_dev_access_record")
print('\n  清理后表内行数: %s' % cur.fetchone()[0])
c.close()
print('\nBENCH DONE')
