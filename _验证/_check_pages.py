# -*- coding: utf-8 -*-
"""页面与链接完整性检查

覆盖：
  ① 路由 ↔ 视图 ↔ 菜单 三者一致
  ② 每个页面调用的接口路径是否都在后端存在（复用 path 检查逻辑）
  ③ 页面写操作覆盖矩阵（有没有只读页）
  ④ 入口页可达性（/、h5.html、view-screen.html、console.html）
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'frontend', 'src')
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java')
STATIC = os.path.join(ROOT, 'backend', 'src', 'main', 'resources', 'static')

BASE = os.environ.get('BP_BASE', 'http://192.168.31.11:8080')
STRICT = '--strict' in sys.argv

# ---------- 后端接口清单 ----------
backend = set()


def norm(p):
    p = re.sub(r'\$\{[^}]+\}', '{}', p or '')
    p = re.sub(r'\{[^}]*\}', '{}', p)
    p = re.sub(r'/+', '/', p)
    return p.rstrip('/') if len(p) > 1 else p


for root, _, fs in os.walk(JAVA):
    for f in fs:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        base = bm.group(1)
        for m in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping'
                             r'(?:\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?', s):
            backend.add((norm(base + '/' + (m.group(2) or '')).replace('//', '/'),
                         m.group(1).upper()))

# ---------- 路由与视图 ----------
rtext = io.open(os.path.join(SRC, 'router', 'index.js'), encoding='utf-8').read()
routes = []
for m in re.finditer(r"path:\s*'/([a-z\-]+)',[\s\S]{0,400}?component:\s*\(\)\s*=>\s*"
                     r"import\('@/views/(\w+)\.vue'\),[\s\S]{0,200}?meta:\s*\{([^}]*)\}", rtext):
    t = re.search(r"title:\s*'([^']+)'", m.group(3))
    g = re.search(r"group:\s*'([^']+)'", m.group(3))
    routes.append({'path': m.group(1), 'comp': m.group(2),
                   'title': t.group(1) if t else m.group(2),
                   'group': g.group(1) if g else '未分组'})

# ---------- api 模块：方法 → 动词 ----------
api_verbs = {}
_mtext = io.open(os.path.join(SRC, 'api', 'modules.js'), encoding='utf-8').read()
for m in re.finditer(r'export const (\w+Api)\s*=\s*\{(.*?)\n\}', _mtext, re.S):
    name, body = m.group(1), m.group(2)
    methods = {}
    for mm in re.finditer(r'(\w+):\s*\([^)]*\)\s*=>\s*req\.(get|post|put|delete)', body):
        methods[mm.group(1)] = mm.group(2).upper()
    api_verbs[name] = methods

# ---------- 每页调用与写操作 ----------
matrix = []
for r in routes:
    for base_dir in ('views', 'screen'):
        p = os.path.join(SRC, base_dir, r['comp'] + '.vue')
        if os.path.exists(p):
            break
    else:
        p = None
    calls, writes = set(), set()
    if p:
        s = io.open(p, encoding='utf-8').read()
        for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"]([^`'\"]*)", s):
            path = m.group(2)
            if not path.startswith('/api/'):
                path = '/api/v1' + path
            calls.add((norm(path), m.group(1).upper()))
        writes = {c for c in calls if c[1] != 'GET'}
        # 通过 api 模块封装的写操作（req.* 只在 modules.js 里出现）
        for api_name, methods in api_verbs.items():
            if api_name not in s:
                continue
            for meth, verb in methods.items():
                if verb != 'GET' and re.search(r'\.%s\s*\(' % meth, s):
                    writes.add(('api:%s.%s' % (api_name, meth), verb))
    matrix.append({**r, 'file': p, 'calls': len(calls), 'writes': len(writes)})

# ---------- 输出 ----------
print('=' * 78)
print(' 页面与链接完整性检查   %s' % BASE)
print('=' * 78)

issues = []

# ① 路由↔视图↔菜单
print('\n① 路由 / 视图 / 菜单')
missing_file = [r for r in matrix if r['file'] is None or not os.path.exists(r['file'])]
by_group = {}
for r in matrix:
    by_group.setdefault(r['group'], []).append(r)
print('   路由 %d 条 ｜ 分组 %d 个' % (len(routes), len(by_group)))
if missing_file:
    print('   ✗ 视图缺失：%s' % [r['comp'] for r in missing_file])
    issues.append('视图缺失')
else:
    print('   ✔ 所有路由的视图文件均存在')

# ② 菜单渲染：Layout 用 menuRoutes + meta.group
lay = io.open(os.path.join(SRC, 'layout', 'Layout.vue'), encoding='utf-8').read()
rank_paths = set(re.findall(r"'/([a-z\-]+)':\s*\d+", lay))
no_rank = [r['path'] for r in matrix if r['path'] not in rank_paths]
if no_rank:
    print('   ⚠ 未在 MENU_RANK 中排序（会排到末尾）：%s' % ', '.join(no_rank))
else:
    print('   ✔ 全部 %d 个页面均在 MENU_RANK 中定义顺序' % len(matrix))

group_icons = re.findall(r'^\s{2}([\u4e00-\u9fa5]+):\s*[\'"]', lay, re.M)
missing_icon = [g for g in by_group if g not in group_icons and g != '未分组']
if missing_icon:
    print('   ⚠ 分组缺图标：%s' % ', '.join(missing_icon))
else:
    print('   ✔ 分组图标齐全')

# ③ 每页接口路径有效性
print('\n③ 页面调用的接口是否都在后端存在')
bad_calls = {}
dynamic_calls = set()
for r in matrix:
    if not r['file']:
        continue
    s = io.open(r['file'], encoding='utf-8').read()
    for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"]([^`'\"]*)", s):
        path = m.group(2)
        # 模板拼接 / 变量路径无法静态判定，单独统计（需人工核对）
        if '${' in path or 'pathTpl' in path:
            dynamic_calls.add('%s %s' % (m.group(1).upper(), path[:60]))
            continue
        if not path.startswith('/api/'):
            path = '/api/v1' + path
        if (norm(path), m.group(1).upper()) not in backend:
            bad_calls.setdefault(r['title'], set()).add(
                '%s %s' % (m.group(1).upper(), path))
if bad_calls:
    for t, cs in bad_calls.items():
        print('   ✗ %-14s %s' % (t, ', '.join(sorted(cs))))
    issues.append('接口路径不一致')
else:
    print('   ✔ 无失效路径（后端 %d 个接口）' % len(backend))
if dynamic_calls:
    print('   ○ 动态拼接路径 %d 处（静态不可判定，需人工核对）：%s'
          % (len(dynamic_calls), '; '.join(sorted(dynamic_calls)[:3])))

# ④ 写操作覆盖矩阵
print('\n④ 页面写操作覆盖')
readonly = [r for r in matrix if r['writes'] == 0 and r['path'] != 'dashboard']
print('   有写操作 %d 页 ｜ 只读 %d 页' % (len([r for r in matrix if r['writes']]),
                                        len(readonly)))
for r in readonly:
    print('   ○ %-14s /%s' % (r['title'], r['path']))

# ⑤ 入口可达
print('\n⑤ 入口页')
for name, url in (('/', '/'), ('租客端 H5', '/h5.html'),
                  ('全屏大屏', '/view-screen.html'), ('旧验证台', '/console.html')):
    try:
        req = urllib.request.Request(BASE + url, method='GET')
        with urllib.request.urlopen(req, timeout=12) as resp:
            print('   ✔ %-12s %s → HTTP %s' % (name, url, resp.status))
    except urllib.error.HTTPError as e:
        print('   ✗ %-12s %s → HTTP %s' % (name, url, e.code))
        issues.append('入口不可达 ' + url)
    except Exception as e:
        print('   ✗ %-12s %s → %s' % (name, url, type(e).__name__))
        issues.append('入口不可达 ' + url)

# ⑥ 分组清单
print('\n⑥ 菜单结构')
for g in ('运营总览', '资格准入', '配租与合同', '账务收费',
          '退出与监督', '资产与设备', '服务与协同', '组织与系统'):
    items = by_group.get(g, [])
    if items:
        print('   %-8s %d 项：%s' % (g, len(items),
                                   ' → '.join(x['title'] for x in items)))

print('\n' + '-' * 78)
if issues:
    print(' 结论：发现 %d 类问题（%s）' % (len(issues), '、'.join(sorted(set(issues)))))
    sys.exit(1)
print(' 结论：✔ 页面与链接完整')
sys.exit(0)
