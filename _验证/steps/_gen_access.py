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
只灌开门记录（基础数据已就绪）+ 条件化处理 uk_tenant_event
背景：uk_tenant_event 可能已被此前中断的任务删除，需幂等处理。
"""
import pymysql, random, time, sys, datetime


TENANT = '350600'
random.seed(20261016)
N_HOUSE = 5771
N_ACCESS = 300000

conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                       charset='utf8mb4', connect_timeout=10, read_timeout=1800, write_timeout=600)
cur = conn.cursor()

def log(m):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), m)); sys.stdout.flush()

def idx_exists(name):
    cur.execute("""SELECT COUNT(*) FROM information_schema.STATISTICS
                   WHERE TABLE_SCHEMA=%s AND TABLE_NAME='bp_dev_access_record' AND INDEX_NAME=%s""",
                (DB, name))
    return cur.fetchone()[0] > 0

# 校验基础数据就绪
cur.execute("SELECT COUNT(*) FROM bp_asset_house"); n_house = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_dev_device"); n_dev = cur.fetchone()[0]
cur.execute("SELECT id FROM bp_asset_house ORDER BY id")
HOUSE_IDS = [r[0] for r in cur.fetchall()]
cur.execute("SELECT id, org_id FROM bp_asset_space WHERE space_type='ROOM' ORDER BY id")
rooms = cur.fetchall()
ROOM_IDS = [(r[0], r[1]) for r in rooms]
cur.execute("SELECT id FROM bp_iam_org ORDER BY id")
ORG_IDS = [r[0] for r in cur.fetchall()]
log('基础数据: 房源=%d 设备=%d 房间=%d 组织=%d' % (n_house, n_dev, len(ROOM_IDS), len(ORG_IDS)))
assert n_house == N_HOUSE and len(ROOM_IDS) == N_HOUSE, '基础数据不完整，需重跑 _gen_perf_data3.py'

# ---- 幂等处理唯一索引 ----
if idx_exists('uk_tenant_event'):
    log('uk_tenant_event 存在，先删除以加速灌数')
    cur.execute("ALTER TABLE bp_dev_access_record DROP INDEX uk_tenant_event")
    conn.commit()
else:
    log('uk_tenant_event 不存在（此前已删除），继续')

# 清掉可能残留的记录
cur.execute("TRUNCATE TABLE bp_dev_access_record")
conn.commit()
log('已清空开门记录表')

# ---- 灌数据 ----
TRUSTED = ['1001', '1002', '1005', '1006', '1007', '1009', '1049', '1032']
UNTRUSTED = ['1015', '1016', '1017', '1022']
NAMES = {'1049': '人脸开门', '1005': '授权开门(APP在线)', '1002': '授权开门(APP)',
         '1001': '刷卡开门(身份证)', '1007': '蓝牙钥匙', '1017': '普通密码开门',
         '1016': '管理员密码开门', '1015': '机械钥匙开门', '1022': '一次性密码开门'}
T0 = datetime.datetime(2026, 10, 1)
SPAN = int((datetime.datetime(2026, 12, 25) - T0).total_seconds())

AR_COLS = ['id', 'tenant_id', 'event_id', 'device_id', 'device_mac', 'space_id', 'house_id',
           'org_id', 'open_type', 'open_type_name', 'is_trusted', 'person_id',
           'target_user_mobile', 'open_time', 'source', 'is_abnormal', 'abnormal_type']
ph = '(' + ','.join(['%s'] * len(AR_COLS)) + ',NOW(3))'
head = "INSERT INTO bp_dev_access_record(%s,create_time) VALUES " % ','.join('`%s`' % c for c in AR_COLS)

_id = [2000000000000000000]
t0 = time.time(); done = 0
CHUNK = 10000
while done < N_ACCESS:
    n = min(CHUNK, N_ACCESS - done)
    rows = []
    for _ in range(n):
        i = random.randint(0, N_HOUSE - 1)
        trusted = random.random() < 0.88
        ot = random.choice(TRUSTED if trusted else UNTRUSTED)
        _id[0] += 1; aid = _id[0]
        rows.append((aid, TENANT, 'EV%012d' % aid, 'LK%08d' % (i + 1), 'FF00FFE%05d' % (i + 1),
                     ROOM_IDS[i][0], HOUSE_IDS[i], ORG_IDS[i % len(ORG_IDS)], ot, NAMES.get(ot, ot),
                     1 if trusted else 0, None, '138%08d' % (i % 100000000),
                     (T0 + datetime.timedelta(seconds=random.randint(0, SPAN))).strftime('%Y-%m-%d %H:%M:%S'),
                     'CALLBACK', 0, None))
    cur.execute(head + ','.join([ph] * n), [v for r in rows for v in r])
    conn.commit()
    done += n
    el = time.time() - t0
    log('  %7d/%d  %6.1fs (%.0f 行/秒)' % (done, N_ACCESS, el, done / el))

# ---- 重建唯一索引并计时 ----
log('重建唯一索引 uk_tenant_event')
t0 = time.time()
cur.execute("ALTER TABLE bp_dev_access_record ADD UNIQUE KEY uk_tenant_event(tenant_id,event_id,open_time)")
conn.commit()
log('  索引构建耗时 %.1fs' % (time.time() - t0))

cur.execute("ANALYZE TABLE bp_dev_access_record"); conn.commit()

print('\n=== 结果 ===')
cur.execute("SELECT COUNT(*) FROM bp_dev_access_record")
print('  开门记录总数:', cur.fetchone()[0])
cur.execute("""SELECT PARTITION_NAME, TABLE_ROWS, ROUND((DATA_LENGTH+INDEX_LENGTH)/1024/1024,1)
               FROM information_schema.PARTITIONS
               WHERE TABLE_SCHEMA=%s AND TABLE_NAME='bp_dev_access_record'
                 AND PARTITION_NAME IS NOT NULL ORDER BY PARTITION_ORDINAL_POSITION""", (DB,))
print('  分区分布（名称, 估算行数, MB）:')
for r in cur.fetchall():
    print('    %-10s %-10s %s' % r)
cur.execute("""SELECT ROUND(SUM(DATA_LENGTH+INDEX_LENGTH)/1024/1024,1) FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s""", (DB,))
print('  bp_platform 总占用: %s MB' % cur.fetchone()[0])

conn.close()
print('\nACCESS DATA DONE')
