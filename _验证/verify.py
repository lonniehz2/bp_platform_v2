# -*- coding: utf-8 -*-
"""
=====================================================================
 云门道业务平台 · 数据库一键验证入口
=====================================================================
用法：
  python verify.py check                # 连通性 + 版本检查
  python verify.py ddl                  # 执行 P1~P5 建表（115 表）
  python verify.py readback             # 结构回读校验（表数/列数/注释/索引）
  python verify.py smoke                # 冒烟（写读 + 唯一约束 + 分区路由）
  python verify.py data                 # 生成压测数据
  python verify.py perf                 # 查询性能与执行计划
  python verify.py all                  # = check + ddl + readback + smoke
  python verify.py full                 # = all + data + perf
  python verify.py clean                # 删除测试库（危险，需确认）

  python verify.py check -c other.json  # 指定其它配置文件

退出码：0=全部通过，1=有失败
=====================================================================
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


# ============ check：连通性 ============
def cmd_check(cfg):
    C.title('步骤 0 · 连通性与版本检查')
    db = cfg['db']
    print('  目标: %s:%s / %s' % (db['host'], db['port'], db['database']))
    try:
        conn = C.connect(cfg, database=None, timeout=8)
    except Exception as e:
        print('  ' + C.err('连接失败: %s' % e))
        print('\n  请检查：')
        print('   1) 网络是否与数据库同网段（家庭网/公司网切换常见原因）')
        print('   2) 修改 _验证/config.json 中的 host / port')
        print('   3) 数据库服务是否运行')
        return False

    ok_all = True
    with conn.cursor() as cur:
        def one(label, sql):
            try:
                cur.execute(sql)
                r = cur.fetchone()
                print('  %-30s %s' % (label, r[0] if r else None))
                return r[0] if r else None
            except Exception as e:
                print('  %-30s %s' % (label, C.err(str(e)[:60])))
                return None

        ver = one('MySQL 版本', 'SELECT VERSION()')
        one('字符集 / 排序规则', "SELECT CONCAT(@@character_set_server,' / ',@@collation_server)")
        one('sql_mode', 'SELECT @@sql_mode')
        one('innodb_buffer_pool_size', "SELECT CONCAT(ROUND(@@innodb_buffer_pool_size/1024/1024),' MB')")
        one('local_infile', 'SELECT @@local_infile')

        # 排序规则可用性（DDL 依赖）
        cur.execute("SELECT COUNT(*) FROM information_schema.COLLATIONS "
                    "WHERE COLLATION_NAME='utf8mb4_0900_ai_ci'")
        has = cur.fetchone()[0] == 1
        print('  %-30s %s' % ('utf8mb4_0900_ai_ci 可用', C.ok('是') if has else C.err('否')))
        if not has:
            ok_all = False

        # 已有库
        cur.execute('SHOW DATABASES')
        dbs = [r[0] for r in cur.fetchall()]
        user_dbs = [d for d in dbs if d not in
                    ('information_schema', 'mysql', 'performance_schema', 'sys')]
        print('  %-30s %s' % ('非系统库', ', '.join(user_dbs) if user_dbs else '(无)'))
        print('  %-30s %s' % ('目标库 bp_platform', '已存在' if db['database'] in dbs else '不存在（将由 ddl 创建）'))

        # 若库已存在，报当前表数
        if db['database'] in dbs:
            cur.execute("SELECT COUNT(*) FROM information_schema.TABLES "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'", (db['database'],))
            n = cur.fetchone()[0]
            exp = cfg['expect']['tables']
            mark = C.ok('符合') if n == exp else C.warn('与期望 %d 不符' % exp)
            print('  %-30s %d 表 (%s)' % ('当前表数', n, mark))

    conn.close()

    # 版本提示
    if ver and str(ver).startswith('5.'):
        print('\n  ' + C.err('警告：检测到 MySQL 5.x，本 DDL 依赖 8.0+ 特性（utf8mb4_0900_ai_ci），将失败'))
        ok_all = False
    return ok_all


# ============ ddl ============
def cmd_ddl(cfg):
    C.title('步骤 1 · 执行 DDL（P1~P5）')
    r = C.run_step('_run_ddl.py', cfg)
    return r.passed


# ============ readback ============
def cmd_readback(cfg):
    C.title('步骤 2 · 结构回读校验')
    r = C.run_step('_verify_db.py', cfg)
    if not r.passed:
        return False

    # 主进程再断言一次关键指标
    C.title('步骤 2b · 关键指标断言')
    exp = cfg['expect']
    db = cfg['db']
    try:
        conn = C.connect(cfg)
        cur = conn.cursor()
        passed = True

        cur.execute("SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'", (db['database'],))
        n_tab = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN COLUMN_COMMENT<>'' THEN 1 ELSE 0 END) "
                    "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s", (db['database'],))
        n_col, n_cmt = cur.fetchone()
        n_col, n_cmt = int(n_col), int(n_cmt)
        cov = 100.0 * n_cmt / n_col if n_col else 0

        cur.execute("""SELECT t.TABLE_NAME FROM information_schema.TABLES t
                       LEFT JOIN (SELECT DISTINCT TABLE_NAME FROM information_schema.STATISTICS
                                  WHERE TABLE_SCHEMA=%s AND INDEX_NAME='PRIMARY') p
                         ON t.TABLE_NAME=p.TABLE_NAME
                       WHERE t.TABLE_SCHEMA=%s AND t.TABLE_TYPE='BASE TABLE'
                         AND p.TABLE_NAME IS NULL""", (db['database'], db['database']))
        no_pk = [x[0] for x in cur.fetchall()]

        cur.execute("""SELECT COUNT(*) FROM information_schema.PARTITIONS
                       WHERE TABLE_SCHEMA=%s AND TABLE_NAME='bp_dev_access_record'
                         AND PARTITION_NAME IS NOT NULL""", (db['database'],))
        n_part = int(cur.fetchone()[0])

        def chk(label, actual, expect_v, cmp='=='):
            nonlocal passed
            if cmp == '==':
                good = actual == expect_v
            elif cmp == '>=':
                good = actual >= expect_v
            else:
                good = True
            print('  %-32s %-10s 期望 %-10s %s' %
                  (label, actual, expect_v, C.ok('OK') if good else C.err('FAIL')))
            if not good:
                passed = False

        chk('表数量', n_tab, exp['tables'])
        chk('列数量', n_col, exp['columns'])
        chk('列注释覆盖率(%)', round(cov, 2), exp['comment_coverage'])
        chk('缺主键表数', len(no_pk), 0)
        chk('分区表分区数', n_part, 7)
        if no_pk:
            print('    缺主键: %s' % no_pk[:10])
        conn.close()
        return passed
    except Exception as e:
        print('  ' + C.err('断言失败: %s' % e))
        return False


# ============ smoke ============
def cmd_smoke(cfg):
    C.title('步骤 3 · 冒烟测试')
    r = C.run_step('_smoke.py', cfg)
    return r.passed


# ============ data ============
def cmd_data(cfg):
    C.title('步骤 4 · 生成压测数据')
    print(C.dim('  说明：数据量由 config.json 的 data 段控制；当前实现为固定规模'))
    ok1 = C.run_step('_gen_perf_data3.py', cfg).passed
    ok2 = C.run_step('_gen_access.py', cfg).passed
    return ok1 and ok2


# ============ perf ============
def cmd_perf(cfg):
    C.title('步骤 5 · 查询性能与执行计划')
    ok1 = C.run_step('_perf_test2.py', cfg).passed
    ok2 = C.run_step('_perf_workorder.py', cfg).passed
    return ok1 and ok2


# ============ clean ============
def cmd_clean(cfg):
    C.title('危险操作 · 删除测试库')
    db = cfg['db']['database']
    print('  将执行: DROP DATABASE `%s`' % db)
    ans = input('  请输入库名以确认: ').strip()
    if ans != db:
        print('  ' + C.warn('已取消'))
        return False
    try:
        conn = C.connect(cfg, database=None)
        with conn.cursor() as cur:
            cur.execute('DROP DATABASE IF EXISTS `%s`' % db)
        conn.commit(); conn.close()
        print('  ' + C.ok('已删除 %s' % db))
        return True
    except Exception as e:
        print('  ' + C.err('删除失败: %s' % e))
        return False


# ============ 组合 ============
def run_all(cfg, with_data=False):
    results = []
    t0 = __import__('time').time()

    ok_check = cmd_check(cfg)
    print()
    if not ok_check:
        C.title('中止')
        print('  ' + C.err('连通性检查未通过，后续步骤不再执行'))
        return False

    ok_ddl = cmd_ddl(cfg)
    ok_rb = cmd_readback(cfg) if ok_ddl else False
    ok_smoke = cmd_smoke(cfg) if ok_rb else False

    steps = [('check', ok_check, 0), ('ddl', ok_ddl, 0), ('readback', ok_rb, 0), ('smoke', ok_smoke, 0)]

    if with_data and ok_smoke:
        ok_data = cmd_data(cfg)
        ok_perf = cmd_perf(cfg) if ok_data else False
        steps += [('data', ok_data, 0), ('perf', ok_perf, 0)]

    C.title('最终结果')
    all_ok = True
    for name, passed, _ in steps:
        print('  %-14s %s' % (name, C.ok('PASS') if passed else C.err('FAIL')))
        all_ok = all_ok and passed
    print()
    print('  总耗时 %.1fs' % (__import__('time').time() - t0))
    if all_ok:
        print('  ' + C.ok(C.bold('✔ 全部通过，可以进入功能验证')))
    else:
        print('  ' + C.err(C.bold('✘ 存在失败，请按上方提示修复')))
    return all_ok


def main():
    ap = argparse.ArgumentParser(
        description='云门道业务平台 · 数据库一键验证',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument('command', nargs='?', default='help',
                    choices=['check', 'ddl', 'readback', 'smoke', 'data', 'perf',
                             'all', 'full', 'clean', 'help'])
    ap.add_argument('-c', '--config', default=None, help='配置文件路径（默认 config.json）')
    args = ap.parse_args()

    if args.command == 'help':
        print(__doc__)
        return 0

    cfg = C.load_config(args.config)

    try:
        if args.command == 'check':     ok = cmd_check(cfg)
        elif args.command == 'ddl':     ok = cmd_ddl(cfg)
        elif args.command == 'readback':ok = cmd_readback(cfg)
        elif args.command == 'smoke':   ok = cmd_smoke(cfg)
        elif args.command == 'data':    ok = cmd_data(cfg)
        elif args.command == 'perf':    ok = cmd_perf(cfg)
        elif args.command == 'clean':   ok = cmd_clean(cfg)
        elif args.command == 'all':     ok = run_all(cfg, with_data=False)
        elif args.command == 'full':    ok = run_all(cfg, with_data=True)
        else:                           ok = False
    except KeyboardInterrupt:
        print('\n' + C.warn('已中断'))
        return 130

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
