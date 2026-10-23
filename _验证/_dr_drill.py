# -*- coding: utf-8 -*-
"""备份恢复演练：全库逻辑备份 → 恢复到临时库 → 逐表比对行数。

用途：验证「数据库备份可恢复」这一上线前置条件，而不是只确认"有备份"。

用法：
  python _dr_drill.py            # 演练并清理临时库
  python _dr_drill.py --keep     # 保留恢复库供人工检查
  python _dr_drill.py --skip-dev # 跳过最大的门禁记录表（快速演练）
"""
import sys
import time

import pymysql

SRC = dict(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
           database='bp_platform', charset='utf8mb4')
DST_DB = 'bp_restore_check'
KEEP = '--keep' in sys.argv
TABLES = None
for _a in sys.argv:
    if _a.startswith('--tables='):
        TABLES = [x.strip() for x in _a.split('=', 1)[1].split(',') if x.strip()]
SKIP_DEV = '--skip-dev' in sys.argv

BATCH = 2000


def conn(database=None):
    kw = dict(host=SRC['host'], port=SRC['port'], user=SRC['user'],
              password=SRC['password'], charset='utf8mb4')
    if database:
        kw['database'] = database
    return pymysql.connect(**kw)


def tables(cur):
    cur.execute("""select table_name from information_schema.tables
                   where table_schema=%s and table_type='BASE TABLE'
                   order by table_name""", (SRC['database'],))
    return [r[0] for r in cur.fetchall()]


def create_sql(cur, t):
    cur.execute('show create table `%s`' % t)
    return cur.fetchone()[1]


def copy_table(src_cur, dst_cur, t):
    """按主键分页复制，避免 OFFSET 深翻页。"""
    src_cur.execute('show columns from `%s`' % t)
    cols = [r[0] for r in src_cur.fetchall()]
    pk = 'id' if 'id' in cols else None
    collist = ','.join('`%s`' % c for c in cols)
    ph = ','.join(['%s'] * len(cols))
    total = 0
    if pk:
        last = None
        while True:
            if last is None:
                src_cur.execute('select %s from `%s` order by `%s` limit %d'
                                % (collist, t, pk, BATCH))
            else:
                src_cur.execute('select %s from `%s` where `%s` > %%s order by `%s` '
                                'limit %d' % (collist, t, pk, pk, BATCH), (last,))
            rows = src_cur.fetchall()
            if not rows:
                break
            dst_cur.executemany('insert into `%s` (%s) values (%s)'
                                % (t, collist, ph), rows)
            total += len(rows)
            last = rows[-1][cols.index(pk)]
    else:
        src_cur.execute('select %s from `%s`' % (collist, t))
        while True:
            rows = src_cur.fetchmany(BATCH)
            if not rows:
                break
            dst_cur.executemany('insert into `%s` (%s) values (%s)'
                                % (t, collist, ph), rows)
            total += len(rows)
    return total


def main():
    t0 = time.time()
    src = conn(SRC['database'])
    sc = src.cursor()
    all_tables = tables(sc)
    if TABLES:
        all_tables = [t for t in all_tables if t in TABLES]
    if SKIP_DEV:
        all_tables = [t for t in all_tables if t != 'bp_dev_access_record']
    print('源库表数: %d（跳过门禁记录表: %s）' % (len(all_tables), SKIP_DEV))

    adm = conn()
    ac = adm.cursor()
    ac.execute('drop database if exists `%s`' % DST_DB)
    ac.execute('create database `%s` default charset utf8mb4' % DST_DB)
    adm.commit()

    dst = conn(DST_DB)
    dc = dst.cursor()
    dc.execute('set foreign_key_checks=0')

    created = copied = 0
    for t in all_tables:
        ddl = create_sql(sc, t)
        dc.execute(ddl)
        created += 1
    dst.commit()
    print('建表完成: %d 张，用时 %.1fs' % (created, time.time() - t0))

    t1 = time.time()
    for t in all_tables:
        n = copy_table(sc, dc, t)
        copied += n
        print('  %-38s %6d 行' % (t, n))
    dst.commit()
    print('复制数据: %d 行，用时 %.1fs' % (copied, time.time() - t1))

    # 比对行数
    mismatch = []
    for t in all_tables:
        sc.execute('select count(*) from `%s`' % t)
        a = sc.fetchone()[0]
        dc.execute('select count(*) from `%s`' % t)
        b = dc.fetchone()[0]
        if a != b:
            mismatch.append((t, a, b))

    print('\n逐表比对：%d 张表' % len(all_tables))
    if mismatch:
        print('不一致 %d 张：' % len(mismatch))
        for t, a, b in mismatch[:15]:
            print('  %-40s 源 %d / 恢复 %d' % (t, a, b))
    else:
        print('全部一致 ✔')

    if not KEEP:
        ac.execute('drop database `%s`' % DST_DB)
        adm.commit()
        print('临时库已清理（--keep 可保留）')
    else:
        print('临时库保留：%s' % DST_DB)

    print('\n总耗时 %.1fs，结论：%s'
          % (time.time() - t0, '恢复演练通过' if not mismatch else '存在不一致，需排查'))
    src.close()
    dst.close()
    adm.close()
    return 0 if not mismatch else 1


if __name__ == '__main__':
    raise SystemExit(main())
