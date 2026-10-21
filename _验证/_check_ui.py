# -*- coding: utf-8 -*-
"""UI 自动化冒烟测试（包装器）

从路由表生成待测页面清单，调用 node ui_smoke.js 驱动本机 Edge 逐页检查，
汇总输出通过/失败清单。

用法：
  python _check_ui.py            # 全量
  python _check_ui.py --strict   # 有失败返回非 0
  python _check_ui.py --only 5   # 只测前 5 个页面（快速自检）
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
ROUTER = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
BASE = os.environ.get('BP_BASE', 'http://192.168.31.11:8080')
STRICT = '--strict' in sys.argv
ONLY = None
for i, a in enumerate(sys.argv):
    if a == '--only' and i + 1 < len(sys.argv):
        ONLY = int(sys.argv[i + 1])

# 需要较慢等待的页面（图表/聚合统计）
SLOW = {'/dashboard', '/reports', '/screen'}


def build_routes():
    s = io.open(ROUTER, encoding='utf-8').read()
    out = []
    # path 允许带可选参数（如 '/rbac/:tab?'）：以前的正则只认单段纯字母，
    # 加了 tab 参数的路由会被静默漏掉，导致冒烟页数「看起来」变少。
    # 这里按「基础路径」登记（不带参数时落到默认 tab）；
    # 各 tab 的深链覆盖由 _check_tab_routes.js 专项负责。
    for m in re.finditer(r"path:\s*'([^']+)',[\s\S]{0,400}?"
                         r"component:\s*\(\)\s*=>\s*import\('@/views/(\w+)\.vue'\),"
                         r"[\s\S]{0,200}?meta:\s*\{([^}]*)\}", s):
        # 带可选参数的路由（'/rbac/:tab?'）取参数前的基础路径；
        # 不带参数时落到默认 tab，各 tab 深链由 _check_tab_routes.js 专项覆盖。
        path = m.group(1).split('/:')[0]
        if not path.startswith('/'):
            continue
        t = re.search(r"title:\s*'([^']+)'", m.group(3))
        out.append({
            'path': path,
            'title': t.group(1) if t else m.group(2),
            'wait': 3200 if path in SLOW else 1800
        })
    return out


def main():
    routes = build_routes()
    if ONLY:
        routes = routes[:ONLY]
    print('=' * 78)
    print(' UI 自动化冒烟  %s  （%d 个页面）' % (BASE, len(routes)))
    print('=' * 78)

    rj = os.path.join(HERE, '_ui_routes.json')
    io.open(rj, 'w', encoding='utf-8').write(
        json.dumps(routes, ensure_ascii=False, indent=1))

    env = dict(os.environ)
    env['NODE_PATH'] = os.path.join(HERE, 'node_modules')
    p = subprocess.run(['node', os.path.join(HERE, 'ui_smoke.js'),
                        rj, HERE, BASE], cwd=HERE, env=env)

    rep_path = os.path.join(HERE, 'ui-smoke.json')
    if not os.path.exists(rep_path):
        print('✗ 未生成报告')
        return 2

    rep = json.load(io.open(rep_path, encoding='utf-8'))
    print('\n' + '-' * 78)
    print(' 通过 %d / %d' % (rep.get('ok', 0), rep.get('total', 0)))
    if rep.get('failed'):
        print(' 失败清单：')
        for f in rep['failed']:
            print('   ✗ %-22s %s' % (f.get('path'), f.get('title')))
            for x in (f.get('fail') or [])[:2]:
                print('       ' + str(x)[:110])
    print(' 截图目录：%s' % os.path.join(HERE, 'ui-shots'))
    print('-' * 78)

    bad = len(rep.get('failed') or [])
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
