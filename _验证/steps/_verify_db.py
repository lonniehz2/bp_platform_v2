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
"""回读验证：把真实库结构与设计文档期望对比"""
import pymysql


conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                       charset='utf8mb4', connect_timeout=8, read_timeout=60)
cur = conn.cursor()

def q1(sql, args=None):
    cur.execute(sql, args or ())
    r = cur.fetchone()
    return r[0] if r else None

print('=== 1. 表数量 ===')
n_tables = q1("SELECT COUNT(*) FROM information_schema.TABLES "
              "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'", (DB,))
print('  实际表数:', n_tables)

print('\n=== 2. 列数量与注释覆盖 ===')
cur.execute("""SELECT COUNT(*) AS cols,
                      SUM(CASE WHEN COLUMN_COMMENT<>'' THEN 1 ELSE 0 END) AS commented
               FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s""", (DB,))
cols, commented = cur.fetchone()
cols, commented = int(cols), int(commented)
print('  列总数: %d   有注释: %d   覆盖率: %.2f%%' % (cols, commented, 100.0*commented/cols))

print('\n=== 3. 表注释覆盖 ===')
cur.execute("""SELECT COUNT(*), SUM(CASE WHEN TABLE_COMMENT<>'' THEN 1 ELSE 0 END)
               FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'""", (DB,))
tt, tc = cur.fetchone()
print('  表总数: %d   有注释: %d' % (tt, tc))

print('\n=== 4. 库/表排序规则 ===')
print('  库默认:', q1("SELECT DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (DB,)))
cur.execute("""SELECT DISTINCT TABLE_COLLATION FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'""", (DB,))
print('  表排序规则:', [r[0] for r in cur.fetchall()])

print('\n=== 5. 引擎分布 ===')
cur.execute("""SELECT ENGINE, COUNT(*) FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' GROUP BY ENGINE""", (DB,))
for r in cur.fetchall():
    print('  %-10s %d' % (r[0], r[1]))

print('\n=== 6. 索引数量 ===')
n_idx = q1("""SELECT COUNT(DISTINCT TABLE_NAME, INDEX_NAME) FROM information_schema.STATISTICS
              WHERE TABLE_SCHEMA=%s""", (DB,))
print('  索引总数:', n_idx)
n_uniq = q1("""SELECT COUNT(DISTINCT TABLE_NAME, INDEX_NAME) FROM information_schema.STATISTICS
               WHERE TABLE_SCHEMA=%s AND NON_UNIQUE=0""", (DB,))
print('  唯一索引数:', n_uniq)

print('\n=== 7. 主键缺失检查 ===')
cur.execute("""SELECT t.TABLE_NAME FROM information_schema.TABLES t
               LEFT JOIN (SELECT DISTINCT TABLE_NAME FROM information_schema.STATISTICS
                          WHERE TABLE_SCHEMA=%s AND INDEX_NAME='PRIMARY') p
                 ON t.TABLE_NAME=p.TABLE_NAME
               WHERE t.TABLE_SCHEMA=%s AND t.TABLE_TYPE='BASE TABLE' AND p.TABLE_NAME IS NULL""", (DB, DB))
miss_pk = [r[0] for r in cur.fetchall()]
print('  缺主键的表:', miss_pk if miss_pk else '无')

print('\n=== 8. 分区表 ===')
cur.execute("""SELECT TABLE_NAME, COUNT(*) AS parts FROM information_schema.PARTITIONS
               WHERE TABLE_SCHEMA=%s AND PARTITION_NAME IS NOT NULL
               GROUP BY TABLE_NAME""", (DB,))
parts = cur.fetchall()
if parts:
    for r in parts:
        print('  %s : %d 个分区' % (r[0], r[1]))
else:
    print('  无分区表')
cur.execute("""SELECT PARTITION_NAME, PARTITION_DESCRIPTION, TABLE_ROWS
               FROM information_schema.PARTITIONS
               WHERE TABLE_SCHEMA=%s AND TABLE_NAME='bp_dev_access_record'
               ORDER BY PARTITION_ORDINAL_POSITION""", (DB,))
print('  bp_dev_access_record 分区明细:')
for r in cur.fetchall():
    print('    %-10s < %-12s rows=%s' % (r[0], r[1], r[2]))

print('\n=== 9. JSON 列（应为 38 处左右）===')
n_json = q1("""SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA=%s AND DATA_TYPE='json'""", (DB,))
print('  JSON 列数:', n_json)

print('\n=== 10. 按前缀分域统计 ===')
cur.execute("""SELECT SUBSTRING_INDEX(TABLE_NAME,'_',2) AS pfx, COUNT(*)
               FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'
               GROUP BY pfx ORDER BY COUNT(*) DESC""", (DB,))
for r in cur.fetchall():
    print('  %-12s %d' % (r[0], r[1]))

print('\n=== 11. 字符集一致性 ===')
cur.execute("""SELECT DISTINCT CHARACTER_SET_NAME FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA=%s AND CHARACTER_SET_NAME IS NOT NULL""", (DB,))
print('  列字符集:', [r[0] for r in cur.fetchall()])

print('\n=== 12. 大字段与精度抽查 ===')
cur.execute("""SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
               FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN
                 ('bp_asset_house','bp_dev_access_record','bp_grant_task','bp_biz_contract')
                 AND COLUMN_NAME IN
                 ('id','tenant_id','house_status','open_time','event_id','idempotent_key',
                  'contract_status','owner_person_id','legacy_house_id','monthly_rent')
               ORDER BY TABLE_NAME, COLUMN_NAME""", (DB,))
for r in cur.fetchall():
    print('  %-22s %-18s %-16s null=%-3s def=%-6s | %s' % r)

print('\n=== 13. 实例可用性（写读测试，显式雪花 ID）===')
try:
    # 主键无 AUTO_INCREMENT，必须显式提供 id（设计：由应用层生成雪花 ID）
    cur.execute("INSERT INTO bp_iam_tenant(id,tenant_code,tenant_name,tenant_type,"
                "isolation_mode,status,create_by,create_time,update_by,update_time) "
                "VALUES(9100000000000000001,'VERIFY001','校验租户','ORG','ROW','ENABLED','sys',NOW(3),'sys',NOW(3))")
    cur.execute("SELECT id,tenant_code FROM bp_iam_tenant WHERE tenant_code='VERIFY001'")
    r = cur.fetchone()
    print('  插入成功 id=%s code=%s' % r)
    cur.execute("DELETE FROM bp_iam_tenant WHERE tenant_code='VERIFY001'")
    conn.commit()
    print('  清理成功')
except Exception as e:
    print('  写测试失败:', e)

conn.close()
print('\nDONE')
