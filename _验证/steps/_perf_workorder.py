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
"""补充验证：工单闭环时效（漳州标考核项）+ 深分页/导出 索引选择确认"""
import pymysql, json, time, random, datetime


c = pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD, database=DB,
                    charset='utf8mb4', connect_timeout=15, read_timeout=900)
cur = c.cursor()
random.seed(7)

# ---------- 造工单数据（3381 条，对齐漳州标实测规模） ----------
cur.execute("SELECT COUNT(*) FROM bp_ops_workorder")
n0 = cur.fetchone()[0]
print('工单现有行数:', n0)

if n0 < 100:
    cur.execute("SELECT id FROM bp_iam_org")
    orgs = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM bp_asset_house LIMIT 4000")
    houses = [r[0] for r in cur.fetchall()]
    N = 3381
    cols = ['id', 'tenant_id', 'workorder_no', 'order_type', 'order_source', 'org_id', 'house_id',
            'order_title', 'create_time', 'assign_time', 'finish_time', 'close_time',
            'sla_response_minutes', 'sla_finish_minutes', 'sla_status', 'is_device_changed',
            'order_status', 'assign_user_id']
    rows = []
    base = 3000000000000000000
    T = datetime.datetime(2026, 10, 1)
    for i in range(1, N + 1):
        t = T + datetime.timedelta(minutes=random.randint(0, 90 * 24 * 60))
        resp = random.randint(5, 240)          # 响应分钟
        fin = random.randint(resp + 10, resp + 720)
        assign = t + datetime.timedelta(minutes=random.randint(1, 30))
        finish = assign + datetime.timedelta(minutes=fin)
        close = finish + datetime.timedelta(minutes=random.randint(1, 60))
        sla = 'ON_TIME' if resp <= 30 and fin <= 120 else ('RESPONSE_TIMEOUT' if resp > 30 else 'FINISH_TIMEOUT')
        rows.append((base + i, '350600', 'WX%06d' % i, 'REPAIR', 'TENANT_APP',
                     orgs[i % len(orgs)], houses[i % len(houses)], '门锁故障报修%d' % i,
                     t.strftime('%Y-%m-%d %H:%M:%S'), assign.strftime('%Y-%m-%d %H:%M:%S'),
                     finish.strftime('%Y-%m-%d %H:%M:%S'), close.strftime('%Y-%m-%d %H:%M:%S'),
                     30, 120, sla, random.choice([0, 1]), 'CLOSED', 1001 + (i % 50)))
    ph = '(' + ','.join(['%s'] * len(cols)) + ')'
    head = "INSERT INTO bp_ops_workorder(%s) VALUES " % ','.join('`%s`' % x for x in cols)
    t0 = time.time()
    for i in range(0, len(rows), 2000):
        part = rows[i:i + 2000]
        cur.execute(head + ','.join([ph] * len(part)), [v for r in part for v in r])
        c.commit()
    print('工单灌入 %d 条，耗时 %.1fs' % (len(rows), time.time() - t0))
    cur.execute("ANALYZE TABLE bp_ops_workorder"); c.commit()

cur.execute("SELECT COUNT(*) FROM bp_ops_workorder")
print('工单总数:', cur.fetchone()[0])

def run(title, sql, args=()):
    print('\n' + '=' * 74)
    print('■ ' + title)
    try:
        cur.execute('EXPLAIN ' + sql, args)
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            print('  PLAN ' + json.dumps({k: d.get(k) for k in
                  ('table', 'type', 'key', 'key_len', 'rows', 'Extra') if k in d}, ensure_ascii=False))
    except Exception as e:
        print('  PLAN ERR', str(e)[:100])
    t0 = time.time(); cur.execute(sql, args); r = cur.fetchall()
    print('  执行 %.3fs  返回 %d 行' % (time.time() - t0, len(r)))
    return r

# ---------- 工单 SLA 统计（考核数据） ----------
run('W1 工单 SLA 超时统计（按类型）',
    """SELECT order_type, sla_status, COUNT(*) cnt FROM bp_ops_workorder
       WHERE tenant_id='2026' OR tenant_id='350600' GROUP BY order_type, sla_status""")

run('W2 工单闭环时效明细（闭环时间-报修时间，考核"2小时"一票否决）',
    """SELECT workorder_no, create_time, close_time,
              TIMESTAMPDIFF(MINUTE, create_time, close_time) AS close_minutes,
              is_device_changed
       FROM bp_ops_workorder
       WHERE tenant_id='350600' AND close_time IS NOT NULL
       ORDER BY close_minutes DESC LIMIT 20""")

run('W3 超 2 小时未闭环工单（一票否决项筛查）',
    """SELECT COUNT(*) AS over_2h FROM bp_ops_workorder
       WHERE tenant_id='350600' AND close_time IS NOT NULL
         AND TIMESTAMPDIFF(MINUTE, create_time, close_time) > 120""")

run('W4 工单按时率统计（考核导出用）',
    """SELECT COUNT(*) total,
              SUM(CASE WHEN sla_status='ON_TIME' THEN 1 ELSE 0 END) on_time,
              ROUND(SUM(CASE WHEN sla_status='ON_TIME' THEN 1 ELSE 0 END)/COUNT(*)*100,2) on_time_pct
       FROM bp_ops_workorder WHERE tenant_id='350600'""")

run('W5 换锁工单占比（考核"是否换锁"字段）',
    """SELECT is_device_changed, COUNT(*) cnt FROM bp_ops_workorder
       WHERE tenant_id='350600' GROUP BY is_device_changed""")

# ---------- 索引选择问题确认 ----------
print('\n\n########## 索引选择确认 ##########')
run('E1 导出查询（ORDER BY open_time DESC 却选了 uk_tenant_event）',
    """SELECT id, open_time FROM bp_dev_access_record
       WHERE tenant_id='350600' AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-12-01 00:00:00'
       ORDER BY open_time DESC LIMIT 10000""")

run('E2 同样条件但 ORDER BY id（对照）',
    """SELECT id, open_time FROM bp_dev_access_record
       WHERE tenant_id='350600' AND open_time>='2026-10-01 00:00:00' AND open_time<'2026-12-01 00:00:00'
       ORDER BY id DESC LIMIT 10000""")

# ---------- 长事务/连接健康 ----------
print('\n########## 收尾健康检查 ##########')
cur.execute("SELECT COUNT(*) FROM information_schema.INNODB_TRX")
print('  活动事务数:', cur.fetchone()[0])
cur.execute("""SELECT ROUND(SUM(DATA_LENGTH+INDEX_LENGTH)/1024/1024,1) FROM information_schema.TABLES
               WHERE TABLE_SCHEMA=%s""", (DB,))
print('  bp_platform 总占用 MB:', cur.fetchone()[0])

c.close()
print('\nDONE')
