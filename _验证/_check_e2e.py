# -*- coding: utf-8 -*-
"""UI E2E 交互测试（包装器）

用法：
  python _check_e2e.py            # 跑三条闭环
  python _check_e2e.py --strict   # 失败返回非 0
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('BP_BASE', 'http://192.168.31.11:8080')


def main():
    print('=' * 78)
    print(' UI E2E 交互测试  %s' % BASE)
    print('=' * 78)
    env = dict(os.environ)
    env['NODE_PATH'] = os.path.join(HERE, 'node_modules')
    p = subprocess.run(['node', os.path.join(HERE, 'ui_e2e.js'), HERE, BASE],
                       cwd=HERE, env=env)
    rep_path = os.path.join(HERE, 'ui-e2e.json')
    if not os.path.exists(rep_path):
        print('✗ 未生成报告')
        return 2
    rep = json.load(open(rep_path, encoding='utf-8'))
    print('\n' + '-' * 78)
    for r in rep.get('results', []):
        print('  %s %-28s %s' % ('✓' if r['pass'] else '✗', r['name'],
                                 (r.get('detail') or '')[:60]))
    print('-' * 78)
    print(' 通过 %d / %d' % (rep.get('pass', 0), rep.get('total', 0)))
    return 0 if rep.get('pass') == rep.get('total') else 1


if __name__ == '__main__':
    sys.exit(main())
