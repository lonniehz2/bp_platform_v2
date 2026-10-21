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
在真实 MySQL 8.4.11 上原样执行 P1→P5 DDL，逐语句记录成功/失败。
- 自动重建干净库（服务器上本来就只有系统库，bp_platform 不存在）
- 保留完整错误信息（表名 / 行号 / MySQL 错误码）
"""
import pymysql, os, re, io, sys, time



FILES = sorted(f for f in os.listdir(BASE) if re.match(r'^03_数据库设计_P\d.*\.sql$', f))


def connect(db=None):
    return pymysql.connect(host=HOST, port=PORT, user=USER, password=PWD,
                           database=db, charset='utf8mb4',
                           connect_timeout=8, read_timeout=120, write_timeout=60)


def split_statements(sql):
    """按顶层分号切分；跳过纯注释段。DDL 中无存储过程，故无需处理 DELIMITER。"""
    stmts, cur, in_str, in_line_c, in_block_c = [], [], None, False, False
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ''
        if in_line_c:
            if c == '\n':
                in_line_c = False
                cur.append(c)
            i += 1
            continue
        if in_block_c:
            if c == '*' and nxt == '/':
                in_block_c = False
                i += 2
                continue
            i += 1
            continue
        if in_str:
            cur.append(c)
            if c == '\\':
                if i + 1 < n:
                    cur.append(sql[i + 1])
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c == '-' and nxt == '-':
            in_line_c = True
            i += 2
            continue
        if c == '/' and nxt == '*':
            in_block_c = True
            i += 2
            continue
        if c in ("'", '"'):
            in_str = c
            cur.append(c)
            i += 1
            continue
        if c == ';':
            s = ''.join(cur).strip()
            if s:
                stmts.append(s)
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    s = ''.join(cur).strip()
    if s:
        stmts.append(s)
    return stmts


# ---------- 建干净库 ----------
conn = connect()
with conn.cursor() as cur:
    cur.execute("DROP DATABASE IF EXISTS `%s`" % DB)
    cur.execute("CREATE DATABASE `%s` DEFAULT CHARACTER SET utf8mb4 "
                "DEFAULT COLLATE utf8mb4_0900_ai_ci" % DB)
conn.commit()
print('已重建干净库: %s\n' % DB)
conn.close()

# ---------- 逐文件执行 ----------
total_ok, total_fail = 0, 0
failures = []

for fn in FILES:
    path = os.path.join(BASE, fn)
    raw = io.open(path, encoding='utf-8').read()
    stmts = split_statements(raw)
    # 过滤掉库级语句（已处理）
    stmts = [s for s in stmts
             if not re.match(r'^\s*(CREATE\s+DATABASE|USE\s+)', s, re.I)]

    conn = connect(DB)
    ok = fail = 0
    t0 = time.time()
    with conn.cursor() as cur:
        for idx, s in enumerate(stmts, 1):
            head = re.sub(r'\s+', ' ', s[:70])
            try:
                cur.execute(s)
                ok += 1
            except Exception as e:
                fail += 1
                failures.append({
                    'file': fn, 'idx': idx, 'sql_head': head,
                    'err': '%s: %s' % (type(e).__name__, e),
                    'code': getattr(e, 'args', [None])[0],
                })
    conn.commit()
    conn.close()
    dur = time.time() - t0
    total_ok += ok
    total_fail += fail
    print('%-45s 语句=%3d  成功=%3d  失败=%3d  (%.1fs)' % (fn, len(stmts), ok, fail, dur))

print('\n=== 汇总 ===')
print('总语句: %d  成功: %d  失败: %d' % (total_ok + total_fail, total_ok, total_fail))

if failures:
    print('\n=== 失败明细（全部）===')
    for f in failures:
        print('\n[%s #%d] %s' % (f['file'], f['idx'], f['sql_head']))
        print('   -> %s' % f['err'])
else:
    print('\n**所有语句执行成功**')
