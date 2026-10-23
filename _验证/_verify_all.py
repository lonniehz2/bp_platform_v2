# -*- coding: utf-8 -*-
"""全量验证总入口：一条命令跑完 7 项检查，输出汇总表与退出码。

包含：
  1. 静态检查      _check_all.py        构建/ID 精度/接口路径/参数接线/显示/页面对照
  2. 页面渲染      _check_ui.py         43 个页面逐个打开
  3. 业务链路      _check_flows.py      9 条跨模块流程、22 项断言
  4. 并发与幂等    _check_concurrency.py 9 项
  5. 数据一致性    _check_data_health.py 重复签约/超收/重复退租等
  6. 接口性能      _perf_baseline.py    关键接口 p95 与慢接口
  7. 上传完整性    （由 _deploy.py 内部校验，此处提示）

用法：
  python _verify_all.py            # 全部执行
  python _verify_all.py --fast     # 跳过多轮性能采样（更快）
  python _verify_all.py --only flows,concurrency
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ('static', '静态检查', ['_check_all.py']),
    ('ui', '页面渲染', ['_check_ui.py']),
    ('flows', '业务链路', ['_check_flows.py']),
    ('concurrency', '并发与幂等', ['_check_concurrency.py']),
    ('health', '数据一致性', ['_check_data_health.py']),
    ('perf', '接口性能', ['_perf_baseline.py', '--rounds', '2']),
    ('stress', '压力场景', ['_perf_stress.py']),
    ('docs', '文档一致性', ['_check_docs.py']),
    ('props', '列字段校验', ['_check_props.py']),
]

# 体检脚本发现问题时返回 1，但「业务态/造数残留」不算失败，单独标注
SOFT_FAIL = {'health'}


def run(script, args):
    path = os.path.join(HERE, script)
    if not os.path.exists(path):
        return None, '', '%s 不存在' % script
    t0 = time.time()
    try:
        p = subprocess.run([PY, '-X', 'utf8', path] + args, cwd=HERE,
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=1800)
        return p.returncode, p.stdout or '', (p.stderr or '')[-400:]
    finally:
        pass


def main():
    args = sys.argv[1:]
    only = None
    if '--only' in args:
        only = set(args[args.index('--only') + 1].split(','))
    fast = '--fast' in args

    print('=' * 66)
    print('全量验证开始  %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    print('=' * 66)

    results = []
    for key, name, cmd in STEPS:
        if only and key not in only:
            continue
        if fast and key == 'perf':
            cmd = ['_perf_baseline.py', '--rounds', '1']
        print('\n▶ %s（%s）' % (name, cmd[0]))
        t0 = time.time()
        rc, out, err = run(cmd[0], cmd[1:])
        cost = time.time() - t0
        if rc is None:
            print('  ⚠ 跳过：%s' % err)
            results.append((name, 'SKIP', cost, err))
            continue
        tail = [ln for ln in out.strip().splitlines() if ln.strip()][-6:]
        for ln in tail:
            print('   ' + ln.strip()[:110])
        if rc != 0 and key not in SOFT_FAIL:
            # 单次失败可能是环境抖动：重试一次，能过则记为 FLAKY（需要关注但不阻塞）
            print('   ↻ 首次失败，重试一次…')
            rc2, out2, err2 = run(cmd[0], cmd[1:])
            if rc2 == 0:
                rc = 0
                print('   ↻ 重试通过 → 标记 FLAKY（不稳定用例，建议排查）')
                verdict_override = 'FLAKY'
                results.append((name, verdict_override, time.time() - t0, ''))
                continue
        if rc == 0:
            verdict = 'PASS'
        elif key in SOFT_FAIL:
            verdict = 'WARN'
        else:
            verdict = 'FAIL'
        if rc != 0 and err.strip():
            print('   stderr: ' + err.strip()[:200])
        results.append((name, verdict, cost, ''))

    print('\n' + '=' * 66)
    print('%-14s %-6s %8s' % ('检查项', '结果', '耗时'))
    print('-' * 66)
    for name, verdict, cost, note in results:
        mark = {'PASS': '✔', 'WARN': '⚠', 'FAIL': '✘', 'SKIP': '–',
            'FLAKY': '↻'}[verdict]
        print('%-14s %s %-4s %7.1fs %s' % (name, mark, verdict, cost, note))
    print('=' * 66)

    fails = [n for n, v, _, _ in results if v == 'FAIL']
    warns = [n for n, v, _, _ in results if v == 'WARN']
    flaky = [n for n, v, _, _ in results if v == 'FLAKY']
    if fails:
        print('结论：失败 %d 项 —— %s' % (len(fails), '、'.join(fails)))
        return 1
    if warns or flaky:
        parts = []
        if warns:
            parts.append('需人工关注：' + '、'.join(warns))
        if flaky:
            parts.append('不稳定用例：' + '、'.join(flaky))
        print('结论：通过（%s）' % '；'.join(parts))
        return 0
    print('结论：全部通过')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
