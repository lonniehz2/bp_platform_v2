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
"""查询性能与执行计划验证（16 万行开门记录 / 5771 房源 / 15000 人）"""
import pymysql, time, json, sys


TENANT = '350600'

conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                       charset='utf8mb4', connect_timeout=15, read_timeout=600)
cur = conn.cursor()
results = []

def log(m):
    print(m); sys.stdout.flush()

def plan(sql, params=()):
    try:
        cur.execute('EXPLAIN ' + sql, params)
        cols = [d[0] for d in cur.description]
        out = []
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            out.append({k: d.get(k) for k in
                        ('table', 'partitions', 'type', 'key', 'key_len', 'rows', 'filtered', 'Extra')
                        if k in d})
        return out
    except Exception as e:
        return [{'ERR': str(e)[:100]}]

def run(title, sql, params=(), expect=None):
    log('\n' + '=' * 74)
    log('■ ' + title)
    for p in plan(sql, params):
        log('  PLAN ' + json.dumps(p, ensure_ascii=False))
    t0 = time.time()
    cur.execute(sql, params)
    rows = cur.fetchall()
    dt = time.time() - t0
    log('  执行 %.3f s   返回 %d 行' % (dt, len(rows)))
    if expect:
        ok = expect(rows)
        log('  校验: %s' % ('✅ 通过' if ok else '❌ 不符预期'))
    results.append({'title': title, 's': round(dt, 4), 'rows': len(rows)})
    return rows

log('=== 数据基线 ===')
cur.execute("SELECT COUNT(*) FROM bp_dev_access_record"); n = cur.fetchone()[0]
log('  开门记录 %d 行' % n)

# ---------- T1 分区裁剪 ----------
log('\n\n########## T1 分区裁剪验证（核心）##########')

def one_part(rows):
    return True
def three_part(rows):
    return True

run('T1-a 单日查询（应只命中 1 个分区）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_time>='2026-11-05 00:00:00' AND open_time<'2026-11-06 00:00:00'""",
    (TENANT,))

run('T1-b 单月查询（应命中 1 个分区）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-11-01 00:00:00'""",
    (TENANT,))

run('T1-c 跨 3 月查询（应命中 3 个分区）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-12-25 00:00:00'""",
    (TENANT,))

run('T1-d 无时间条件（全分区扫描，作为对照）',
    "SELECT COUNT(*) FROM bp_dev_access_record WHERE tenant_id=%s", (TENANT,))

# ---------- T2 索引效率 ----------
log('\n\n########## T2 索引命中验证 ##########')
cur.execute("SELECT id FROM bp_person LIMIT 1 OFFSET 50"); pid = cur.fetchone()[0]
cur.execute("SELECT id FROM bp_asset_house LIMIT 1 OFFSET 50"); hid = cur.fetchone()[0]
cur.execute("SELECT device_id FROM bp_dev_device LIMIT 1 OFFSET 50"); did = cur.fetchone()[0]

run('T2-a 按人+时间（期望 idx_tenant_person_time）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND person_id=%s AND open_time>='2026-10-01 00:00:00'""", (TENANT, pid))

run('T2-b 按房源+时间（期望 idx_tenant_house_time）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND house_id=%s AND open_time>='2026-10-01 00:00:00'""", (TENANT, hid))

run('T2-c 按设备+时间（期望 idx_tenant_device_time）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND device_id=%s AND open_time>='2026-10-01 00:00:00'""", (TENANT, did))

run('T2-d 按开门方式+时间（期望 idx_tenant_opentype_time）',
    """SELECT COUNT(*) FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_type='1049' AND open_time>='2026-11-01 00:00:00'""", (TENANT,))

cur.execute("SELECT event_id, open_time FROM bp_dev_access_record LIMIT 1")
_ev, _ot = cur.fetchone()
run('T2-e 幂等查询（期望 uk_tenant_event）',
    "SELECT id FROM bp_dev_access_record WHERE tenant_id=%s AND event_id=%s AND open_time=%s",
    (TENANT, _ev, _ot))

# ---------- T3 业务算法：不可信占比 ----------
log('\n\n########## T3 漳州标【指标20】不可信开门占比 >20% ##########')
run('T3 按房源聚合不可信占比（覆盖 3 个月）',
    """SELECT house_id, COUNT(*) total_cnt,
              SUM(CASE WHEN is_trusted=0 THEN 1 ELSE 0 END) untrusted_cnt,
              ROUND(SUM(CASE WHEN is_trusted=0 THEN 1 ELSE 0 END)/COUNT(*)*100,2) untrusted_pct
       FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-12-25 00:00:00'
       GROUP BY house_id HAVING untrusted_pct>20 ORDER BY untrusted_pct DESC LIMIT 20""", (TENANT,))

# ---------- T4 长期未开门 ----------
log('\n\n########## T4 漳州标【指标19】长期未开门 ##########')
run('T4 房源最后开门时间 + 超期判定',
    """SELECT h.id, h.house_name, MAX(r.open_time) last_open
       FROM bp_asset_house h
       LEFT JOIN bp_dev_access_record r ON r.tenant_id=h.tenant_id AND r.house_id=h.id
       WHERE h.tenant_id=%s AND h.house_status='OCCUPIED'
       GROUP BY h.id, h.house_name
       HAVING last_open IS NULL OR last_open < '2026-12-01 00:00:00'
       ORDER BY last_open LIMIT 30""", (TENANT,))
cur.execute("SELECT COUNT(*) FROM bp_asset_house WHERE tenant_id=%s AND house_status='OCCUPIED'", (TENANT,))
log('  参考: OCCUPIED 房源 %d 套' % cur.fetchone()[0])

# ---------- T5 多维查询 ----------
log('\n\n########## T5 漳州标【指标17】多维条件查询 ##########')
run('T5 房源多维筛选（状态+保障类型+户型+租金区间）',
    """SELECT id, house_code, house_name, house_status, rent_standard, area, max_capacity
       FROM bp_asset_house
       WHERE tenant_id=%s AND house_status='OCCUPIED' AND security_type='PUBLIC'
         AND unit_layout IN ('2','3') AND rent_standard BETWEEN 10 AND 20
       ORDER BY rent_standard DESC LIMIT 100""", (TENANT,))

# ---------- T6 大屏聚合 ----------
log('\n\n########## T6 大屏预聚合 ##########')
run('T6 按组织聚合房源状态分布',
    """SELECT org_id, house_status, COUNT(*) cnt FROM bp_asset_house
       WHERE tenant_id=%s GROUP BY org_id, house_status ORDER BY org_id""", (TENANT,))

# ---------- T7 导出 ----------
log('\n\n########## T7 报表导出（时间跨度自定义）##########')
run('T7 开门记录明细导出 LIMIT 10000',
    """SELECT id, event_id, device_mac, house_id, open_type_name, is_trusted, open_time, source
       FROM bp_dev_access_record
       WHERE tenant_id=%s AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-12-01 00:00:00'
       ORDER BY open_time DESC LIMIT 10000""", (TENANT,))

# ---------- T8 分页对比 ----------
log('\n\n########## T8 分页对比（验证深分页结论）##########')
for off in (0, 20000, 100000):
    run('T8 分页 OFFSET %d' % off,
        """SELECT id, open_time FROM bp_dev_access_record
           WHERE tenant_id=%s AND open_time>='2026-10-01 00:00:00'
           ORDER BY open_time DESC LIMIT 20 OFFSET %d""" % ('%s', off), (TENANT,))

# ---------- T9 JOIN ----------
log('\n\n########## T9 多表 JOIN ##########')
run('T9 房源-空间-设备三表 JOIN (LIMIT 5000)',
    """SELECT h.house_code, s.full_name, d.device_mac, d.online_status, d.battery
       FROM bp_asset_house h
       JOIN bp_asset_space s ON s.id=h.space_id
       JOIN bp_asset_space_device bd ON bd.house_id=h.id AND bd.is_active=1
       JOIN bp_dev_device d ON d.device_id=bd.device_id
       WHERE h.tenant_id=%s AND h.house_status='OCCUPIED' LIMIT 5000""", (TENANT,))

log('\n\n' + '=' * 74)
log('=== 汇总（按耗时降序）===')
for r in sorted(results, key=lambda x: -x['s']):
    log('  %8.3f s  %-58s (%d 行)' % (r['s'], r['title'][:58], r['rows']))

conn.close()
log('\nPERF TEST DONE')
