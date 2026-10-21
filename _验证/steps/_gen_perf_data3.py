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
压测数据生成器 v3（修正多值 INSERT 的列/值对应；吞吐约 5000 行/秒）
规模：1 租户 / 20 小区 / 200 栋 / 400 单元 / 5771 房源 / 15000 人 / 5771 锁 / 30 万开门记录
"""
import pymysql, random, time, sys, datetime


TENANT = '350600'
random.seed(20261016)

N_ORG, N_BLD_PER_ORG, N_UNIT_PER_BLD = 20, 10, 2
N_HOUSE, N_PERSON = 5771, 15000
N_ACCESS = 300000

_id = [1000000000000000000]
def nid():
    _id[0] += 1
    return _id[0]

conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                       charset='utf8mb4', connect_timeout=10, read_timeout=1800, write_timeout=600)
cur = conn.cursor()

def log(m):
    print('[%s] %s' % (time.strftime('%H:%M:%S'), m)); sys.stdout.flush()

def ins(table, cols, rows, chunk=10000, label=''):
    """多值 INSERT。cols: 列名列表；rows: 与 cols 等长的元组列表（NOW(3) 也作为字面量写在 cols 里）"""
    if not rows:
        return
    t0 = time.time()
    ncol = len(cols)
    ph = '(' + ','.join(['%s'] * ncol) + ')'
    head = "INSERT INTO `%s`(%s) VALUES " % (table, ','.join('`%s`' % c for c in cols))
    total = 0
    for i in range(0, len(rows), chunk):
        part = rows[i:i + chunk]
        cur.execute(head + ','.join([ph] * len(part)), [v for r in part for v in r])
        conn.commit()
        total += len(part)
    dt = time.time() - t0
    log('  %-24s %7d 行  %6.1fs (%.0f 行/秒)' % (label, total, dt, total / dt if dt else 0))

# ---------------- 清空 ----------------
log('清空测试数据')
cur.execute("SET FOREIGN_KEY_CHECKS=0")
for t in ['bp_dev_access_record', 'bp_dev_device', 'bp_grant_entitlement', 'bp_grant_keyring',
          'bp_asset_space_device', 'bp_asset_space_occupancy', 'bp_asset_house', 'bp_asset_space',
          'bp_person', 'bp_iam_org']:
    cur.execute("TRUNCATE TABLE `%s`" % t)
cur.execute("SET FOREIGN_KEY_CHECKS=1")
conn.commit()
log('已清空')

t_start = time.time()

# ---------------- 租户 ----------------
cur.execute("""INSERT INTO bp_iam_tenant(id,tenant_code,tenant_name,tenant_type,region_code,
    isolation_mode,status,create_by,create_time,update_by,update_time)
    VALUES(%s,%s,'漳州市住房保障中心（压测）','GOV','350600','ROW','ENABLED','sys',NOW(3),'sys',NOW(3))
    ON DUPLICATE KEY UPDATE tenant_name=VALUES(tenant_name)""", (nid(), TENANT))
conn.commit()

# ---------------- 组织 ----------------
ORG_IDS = []; rows = []
for i in range(1, N_ORG + 1):
    oid = nid(); ORG_IDS.append(oid)
    rows.append((oid, TENANT, 'ZZ%04d' % i, '第%d期小区' % i, None, '', 1, 'DISTRICT', 'HOUSING',
                 '福建省漳州市', 117.6 + i * .01, 24.5 + i * .01, i, 'ENABLED', 0, 'sys', 'sys'))
ins('bp_iam_org',
    ['id', 'tenant_id', 'org_code', 'org_name', 'parent_id', 'org_path', 'org_level', 'org_type',
     'supervise_type', 'address', 'longitude', 'latitude', 'sort_no', 'status', 'is_deleted',
     'create_by', 'update_by'],
    rows, 5000, '组织/小区')
# create_time / update_time 已在 DDL 中设默认值，无需显式写入

# ---------------- 空间：楼栋 ----------------
BLD_IDS = []; rows = []
for oi, oid in enumerate(ORG_IDS, 1):
    for b in range(1, N_BLD_PER_ORG + 1):
        bid = nid(); BLD_IDS.append((bid, oid))
        rows.append((bid, TENANT, oid, None, 'ZZ%04d-B%02d' % (oi, b), '%d幢' % b, 'BUILDING', '',
                     '%02d/%02d/' % (oi, b), 2, '第%d期小区%d幢' % (oi, b),
                     round(random.uniform(2000, 8000), 2), b, 'ENABLED', 'sys'))
ins('bp_asset_space',
    ['id', 'tenant_id', 'org_id', 'parent_id', 'space_code', 'space_name', 'space_type',
     'space_path', 'path_code', 'space_level', 'full_name', 'area', 'sort_no', 'status', 'create_by'],
    rows, 5000, '空间-楼栋')

# ---------------- 空间：单元 ----------------
UNIT_IDS = []; rows = []
for bi, (bid, oid) in enumerate(BLD_IDS, 1):
    for u in range(1, N_UNIT_PER_BLD + 1):
        uid = nid(); UNIT_IDS.append((uid, bid, oid))
        rows.append((uid, TENANT, oid, bid, 'U%04d-%02d' % (bi, u), '%d单元' % u, 'UNIT',
                     str(bid) + '/', '%02d/' % u, 3, '第%d幢%d单元' % (bi, u), None, u, 'ENABLED', 'sys'))
ins('bp_asset_space',
    ['id', 'tenant_id', 'org_id', 'parent_id', 'space_code', 'space_name', 'space_type',
     'space_path', 'path_code', 'space_level', 'full_name', 'area', 'sort_no', 'status', 'create_by'],
    rows, 5000, '空间-单元')

# ---------------- 空间：房间 + 房源 ----------------
ROOM_IDS, HOUSE_IDS = [], []
rs, rh = [], []
for h in range(1, N_HOUSE + 1):
    uid, bid, oid = UNIT_IDS[h % len(UNIT_IDS)]
    sid = nid(); hid = nid()
    floor = random.randint(1, 18); room = floor * 100 + random.randint(1, 6)
    area = round(random.uniform(28, 95), 2); rent = round(random.uniform(8, 22), 2)
    ROOM_IDS.append((sid, oid)); HOUSE_IDS.append(hid)
    rs.append((sid, TENANT, oid, uid, 'R%05d' % h, '%d室' % room, 'ROOM', str(uid) + '/',
               '%05d/' % h, 4, '第%05d号房源%d室' % (h, room), area, room, 'ENABLED', 'sys'))
    rh.append((hid, TENANT, oid, sid, 'ZZ-H-%05d' % h, '第%05d号房源%d室' % (h, room),
               'PUBLIC_RENTAL', 'HIGH', 'CIVIL', random.choice(['1', '2', '3']), floor, 'SOUTH',
               area, area, 'FINE',
               random.choice(['PUBLIC', 'PUBLIC', 'PUBLIC', 'AFFORDABLE', 'TALENT']),
               rent, 'AREA_MONTH', random.choice([2, 3, 4]), 0,
               random.choice(['OCCUPIED', 'OCCUPIED', 'OCCUPIED', 'VACANT', 'PENDING_ALLOC']),
               'IN_USE', 'SELF', 'STATE', oid, oid, 'ZZ-H-%05d' % h, 'sys'))
ins('bp_asset_space',
    ['id', 'tenant_id', 'org_id', 'parent_id', 'space_code', 'space_name', 'space_type',
     'space_path', 'path_code', 'space_level', 'full_name', 'area', 'sort_no', 'status', 'create_by'],
    rs, 5000, '空间-房间')
ins('bp_asset_house',
    ['id', 'tenant_id', 'org_id', 'space_id', 'house_code', 'house_name', 'house_type',
     'struct_type', 'use_type', 'unit_layout', 'floor_no', 'orientation', 'area', 'inner_area',
     'decoration', 'security_type', 'rent_standard', 'rent_unit', 'max_capacity', 'current_capacity',
     'house_status', 'use_status', 'manage_nature', 'property_nature', 'owner_org_id', 'admin_org_id',
     'house_alias', 'create_by'],
    rh, 5000, '房源')

# ---------------- 人员 ----------------
rows = []
for p in range(1, N_PERSON + 1):
    rows.append((nid(), TENANT, 'P%06d' % p, '住户%06d' % p, '住户%06d' % p,
                 '138%08d' % (p % 100000000), 'H' + str(p).zfill(20),
                 '330106********%04d' % (p % 10000), random.choice(['M', 'F']),
                 '19%02d-%02d-%02d' % (random.randint(60, 99), random.randint(1, 12), random.randint(1, 28)),
                 random.choice(['VERIFIED', 'VERIFIED', 'UNVERIFIED']),
                 random.choice(['NORMAL'] * 9 + ['BLACKLIST']), ORG_IDS[p % N_ORG], 'sys'))
ins('bp_person',
    ['id', 'tenant_id', 'person_code', 'person_name', 'real_name', 'phone', 'id_card',
     'id_card_mask', 'gender', 'birthday', 'verify_status', 'person_status', 'org_id', 'create_by'],
    rows, 5000, '人员')

# ---------------- 设备 / 门锁 ----------------
rows = []
for i in range(1, N_HOUSE + 1):
    rows.append((nid(), TENANT, 'LK%08d' % i, 'FF00FFE%05d' % i, '门锁-%05d' % i, 'LOCK',
                 'WIFI_LOCK', 'YMD', ORG_IDS[i % N_ORG], ROOM_IDS[i - 1][0], '第%05d号房源' % i,
                 random.choice([1, 1, 1, 1, 0]), random.randint(5, 100),
                 random.choice(['1.0.0', '1.2.0']), random.choice(['V1', 'V2']), 'NORMAL', 'sys'))
ins('bp_dev_device',
    ['id', 'tenant_id', 'device_id', 'device_mac', 'device_name', 'device_type', 'lock_type',
     'ventor', 'org_id', 'space_id', 'install_address', 'online_status', 'battery', 'soft_version',
     'hard_version', 'device_status', 'create_by'],
    rows, 5000, '设备/门锁')

rows = [(nid(), TENANT, ROOM_IDS[i - 1][0], HOUSE_IDS[i - 1], 'LK%08d' % i, 'FF00FFE%05d' % i,
         'LOCK', 'sys') for i in range(1, N_HOUSE + 1)]
ins('bp_asset_space_device',
    ['id', 'tenant_id', 'space_id', 'house_id', 'device_id', 'device_mac', 'device_type', 'create_by'],
    rows, 5000, '空间-设备绑定')

log('基础数据完成，开始灌 %d 条开门记录' % N_ACCESS)

# ---------------- 开门记录 ----------------
cur.execute("ALTER TABLE bp_dev_access_record DROP INDEX uk_tenant_event")
conn.commit()
log('  已临时移除 uk_tenant_event 以加速')

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

t0 = time.time(); done = 0
CHUNK = 10000
while done < N_ACCESS:
    n = min(CHUNK, N_ACCESS - done)
    rows = []
    for _ in range(n):
        i = random.randint(0, N_HOUSE - 1)
        trusted = random.random() < 0.88
        ot = random.choice(TRUSTED if trusted else UNTRUSTED)
        aid = nid()
        rows.append((aid, TENANT, 'EV%012d' % aid, 'LK%08d' % (i + 1), 'FF00FFE%05d' % (i + 1),
                     ROOM_IDS[i][0], HOUSE_IDS[i], ORG_IDS[i % N_ORG], ot, NAMES.get(ot, ot),
                     1 if trusted else 0, None, '138%08d' % (i % 100000000),
                     (T0 + datetime.timedelta(seconds=random.randint(0, SPAN))).strftime('%Y-%m-%d %H:%M:%S'),
                     'CALLBACK', 0, None))
    cur.execute(head + ','.join([ph] * n), [v for r in rows for v in r])
    conn.commit()
    done += n
    if done % 100000 == 0 or done == N_ACCESS:
        el = time.time() - t0
        log('  开门记录 %7d/%d  %6.1fs (%.0f 行/秒)' % (done, N_ACCESS, el, done / el))

log('重建唯一索引 uk_tenant_event')
t0 = time.time()
cur.execute("ALTER TABLE bp_dev_access_record ADD UNIQUE KEY uk_tenant_event(tenant_id,event_id,open_time)")
conn.commit()
log('  索引构建 %.1fs' % (time.time() - t0))

for t in ['bp_dev_access_record', 'bp_asset_house', 'bp_person', 'bp_dev_device', 'bp_asset_space']:
    cur.execute("ANALYZE TABLE %s" % t)
conn.commit()

log('总耗时 %.1fs' % (time.time() - t_start))

print('\n=== 数据规模 ===')
for t in ['bp_iam_org', 'bp_asset_space', 'bp_asset_house', 'bp_person', 'bp_dev_device',
          'bp_asset_space_device', 'bp_dev_access_record']:
    cur.execute("SELECT COUNT(*) FROM `%s`" % t)
    print('  %-26s %8d 行' % (t, cur.fetchone()[0]))
cur.execute("""SELECT ROUND(SUM(DATA_LENGTH+INDEX_LENGTH)/1024/1024,1) FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s""", (DB,))
print('  bp_platform 占用: %s MB' % cur.fetchone()[0])
cur.execute("""SELECT PARTITION_NAME, TABLE_ROWS FROM information_schema.PARTITIONS
               WHERE TABLE_SCHEMA=%s AND TABLE_NAME='bp_dev_access_record'
                 AND PARTITION_NAME IS NOT NULL ORDER BY PARTITION_ORDINAL_POSITION""", (DB,))
print('  分区分布:', [(r[0], r[1]) for r in cur.fetchall()])

conn.close()
print('\nGENERATE DONE')
