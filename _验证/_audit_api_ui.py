# -*- coding: utf-8 -*-
"""前后端匹配核对：后端接口 ↔ 前端调用 ↔ 页面。

输出三类结论：
  A. 前端调用但后端没有（应为空；有则是路径写错或接口缺失）
  B. 后端有但前端从未调用（可能是「缺页面/缺入口」，也可能是回调/内部接口）
  C. 按控制器统计覆盖率，并列出「零引用控制器」（很可能缺整块功能）

用法：
  python _audit_api_ui.py            # 控制台报告
  python _audit_api_ui.py --md out.md  # 同时输出 Markdown
"""
import io
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BACKEND = os.path.join(ROOT, 'backend', 'src', 'main', 'java')
FRONTEND = os.path.join(ROOT, 'frontend', 'src')

# ---------------- 1) 后端接口 ----------------
MAPPING_RE = re.compile(r'@(?:[\w.]+\.)?(Get|Post|Put|Delete|Patch)Mapping\s*(?:\(([^)]*)\))?')
BASE_RE = re.compile(r'@RequestMapping\s*\(\s*"([^"]+)"')
PERM_RE = re.compile(r'@(?:com\.yundao\.bp\.iam\.security\.)?RequirePerm\s*\(\s*"([^"]+)"')


def norm_path(p):
    """统一成 /x/{var} 形式，去掉数组/空参等杂音。"""
    p = p.strip()
    m = re.search(r'"([^"]*)"', p)
    if m:
        p = m.group(1)
    p = p.strip().strip('"')
    p = re.sub(r'\{[^}]*\}', '{x}', p)
    if p and not p.startswith('/'):
        p = '/' + p
    if len(p) > 1 and p.endswith('/'):
        p = p[:-1]
    return p


backend = []      # (method, full_path, controller, java_method, perm)
for dirpath, _dirs, files in os.walk(BACKEND):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        path = os.path.join(dirpath, fn)
        src = io.open(path, encoding='utf-8', errors='replace').read()
        m = BASE_RE.search(src)
        base = norm_path(m.group(1)) if m else ''
        cls = fn[:-5]
        # 逐个方法解析
        for mm in MAPPING_RE.finditer(src):
            method = mm.group(1).upper()
            sub = norm_path(mm.group(2) or '')
            full = (base + sub) if sub else base
            # 去掉统一前缀，与前端相对路径对齐
            if full.startswith('/api/v1'):
                full = full[len('/api/v1'):] or '/'

            # 方法名：取 ) { 之前的标识符
            tail = src[mm.end():mm.end() + 400]
            name_m = re.search(r'\b(\w+)\s*\(', tail)
            java_method = name_m.group(1) if name_m else '?'
            # 权限：映射前 200 字符内
            before = src[max(0, mm.start() - 300):mm.start()]
            perm_m = PERM_RE.search(before)
            backend.append((method, full, cls, java_method,
                            perm_m.group(1) if perm_m else ''))

# ---------------- 2) 前端调用 ----------------
CALL_RE = re.compile(r"\breq\.(get|post|put|delete)\s*\(([^\n]{0,200})")
front = []       # (method, path, file)
for dirpath, _dirs, files in os.walk(FRONTEND):
    for fn in files:
        if not fn.endswith(('.js', '.vue')):
            continue
        path = os.path.join(dirpath, fn)
        src = io.open(path, encoding='utf-8', errors='replace').read()
        rel = os.path.relpath(path, FRONTEND).replace('\\', '/')
        for mm in CALL_RE.finditer(src):
            method = mm.group(1).upper()
            expr = mm.group(2)
            # 截到第一个顶层逗号/右括号，避免把 body 参数一起吃进来
            depth, cut = 0, len(expr)
            for i, ch in enumerate(expr):
                if ch in '([{':
                    depth += 1
                elif ch in ')]}':
                    if depth == 0:
                        cut = i
                        break
                    depth -= 1
                elif ch == ',' and depth == 0:
                    cut = i
                    break
            expr = expr[:cut]
            e2 = re.sub(r'\$\{[^}]*\}', '{x}', expr)
            if '+' in e2:
                # 按 + 切分：带引号的是字面量，其余是变量 → {x}
                parts = re.split(r'\s*\+\s*', e2)
                buf = []
                for part in parts:
                    m2 = re.match(r"^[`'\"]([^`'\"]*)[`'\"]$", part.strip())
                    if m2:
                        if m2.group(1):
                            buf.append(m2.group(1))
                    else:
                        buf.append('{x}')
                p = '/'.join(x.strip('/') for x in buf if x.strip('/'))
                p = '/' + p if p else '/'
            else:
                segs = re.findall(r"[`'\"]([^`'\"]*)[`'\"]", e2)
                if not segs:
                    continue
                p = ''.join(segs)
            p = re.sub(r'\{[^}]*\}', '{x}', p)
            p = p.split('?')[0]
            if not p.startswith('/'):
                p = '/' + p
            p = re.sub(r'/+', '/', p)
            if len(p) > 1 and p.endswith('/'):
                p = p[:-1]
            front.append((method, p, rel))

# ---------------- 3) 匹配 ----------------
def full(p):
    return '/api/v1' + p


# 前端源码里出现过的「路径字面量」（含通过变量传给通用请求函数的情况，
# 例如 actReason(row, '/api/v1/complaints/{id}/close')）
ref_paths = set()
for dirpath, _dirs, files in os.walk(FRONTEND):
    for fn in files:
        if not fn.endswith(('.js', '.vue')):
            continue
        src = io.open(os.path.join(dirpath, fn), encoding='utf-8',
                      errors='replace').read()
        for m in re.finditer(r"[`'\"]((?:/api/v1)?/[a-z][^`'\"\s]*)", src):
            p = m.group(1)
            p = re.sub(r'\$\{[^}]*\}', '{x}', p)
            p = re.sub(r'\{[^}]*\}', '{x}', p)
            p = p.split('?')[0]
            if p.startswith('/api/v1'):
                p = p[len('/api/v1'):] or '/'
            p = re.sub(r'/+', '/', p)
            if len(p) > 1 and p.endswith('/'):
                p = p[:-1]
            ref_paths.add(p)

bmap = {}
for method, p, cls, jm, perm in backend:
    bmap.setdefault((method, p), []).append((cls, jm, perm))

fmap = {}
for method, p, rel in front:
    fmap.setdefault((method, p), []).append(rel)

# A. 前端有、后端无（GET 与 POST 偶尔互换，做一次宽松匹配）
missing_backend = []
for (method, p), rels in sorted(fmap.items()):
    if (method, p) in bmap:
        continue
    alt = 'GET' if method == 'POST' else 'POST'
    if (alt, p) in bmap:
        continue
    missing_backend.append((method, p, sorted(set(rels))[:3]))

# B. 后端有、前端无
unused = []
for (method, p), metas in sorted(bmap.items()):
    if (method, p) in fmap:
        continue
    # 路径字面量出现过（可能由通用函数按变量调用），视为已接线
    if p in ref_paths:
        continue
    # 子路径可能由父路径覆盖（如 /bills/{x} 与 /bills）
    parent = p.rsplit('/', 1)[0]
    if parent and (method, parent) in fmap:
        continue
    unused.append((method, p, metas))

# C. 控制器覆盖率
by_cls = {}
for (method, p), metas in bmap.items():
    for cls in {m[0] for m in metas}:
        by_cls.setdefault(cls, {'total': 0, 'used': 0})
        by_cls[cls]['total'] += 1
        if (method, p) in fmap or (p.rsplit('/', 1)[0], method) in {
                (k[1], k[0]) for k in fmap}:
            by_cls[cls]['used'] += 1

zero_cls = sorted([c for c, v in by_cls.items() if v['used'] == 0])

# ---------------- 4) 输出 ----------------
def pct(a, b):
    return 0 if not b else round(a * 100.0 / b, 1)


print('=' * 76)
print('前后端匹配核对')
print('=' * 76)
print('后端接口 %d 个（%d 个控制器）  前端调用 %d 处（%d 个唯一路径）'
      % (len(bmap), len({m[0] for metas in bmap.values() for m in metas}),
         len(front), len(fmap)))

print('\n[A] 前端调用但后端无（应为 0）：%d' % len(missing_backend))
for method, p, rels in missing_backend[:20]:
    print('  ✗ %-6s %-46s %s' % (method, p, ','.join(rels)))

print('\n[B] 后端有但前端未调用：%d' % len(unused))
for method, p, metas in unused:
    cls, jm, perm = metas[0]
    print('  · %-6s %-46s %s#%s  %s' % (method, p, cls, jm, perm))

print('\n[C] 零引用控制器（很可能缺整块前端）：%d' % len(zero_cls))
for c in zero_cls:
    print('  ✗ %s（%d 个接口）' % (c, by_cls[c]['total']))

print('\n[D] 控制器覆盖率（低覆盖优先关注）：')
rows = sorted(by_cls.items(), key=lambda kv: pct(kv[1]['used'], kv[1]['total']))
for cls, v in rows:
    print('  %-34s %3d/%-3d  %5.1f%%' % (cls, v['used'], v['total'],
                                         pct(v['used'], v['total'])))

# ---------------- 5) Markdown ----------------
if '--md' in sys.argv:
    out = sys.argv[sys.argv.index('--md') + 1]
    L = []
    L.append('# 前后端接口与页面匹配核对')
    L.append('')
    L.append('自动生成：`_验证/_audit_api_ui.py`')
    L.append('')
    L.append('| 指标 | 数量 |')
    L.append('|---|---|')
    L.append('| 后端接口 | %d |' % len(bmap))
    L.append('| 前端调用处 | %d |' % len(front))
    L.append('| 前端调用但后端无 | %d |' % len(missing_backend))
    L.append('| 后端有但前端未调用 | %d |' % len(unused))
    L.append('| 零引用控制器 | %d |' % len(zero_cls))
    L.append('')
    L.append('## A 前端调用但后端无')
    L.append('')
    if missing_backend:
        L.append('| 方法 | 路径 | 调用方 |')
        L.append('|---|---|---|')
        for method, p, rels in missing_backend:
            L.append('| %s | `%s` | %s |' % (method, p, ', '.join(rels)))
    else:
        L.append('无。')
    L.append('')
    L.append('## B 后端有但前端未调用')
    L.append('')
    if unused:
        L.append('| 方法 | 路径 | 控制器#方法 | 权限 |')
        L.append('|---|---|---|---|')
        for method, p, metas in unused:
            cls, jm, perm = metas[0]
            L.append('| %s | `%s` | %s#%s | `%s` |' % (method, p, cls, jm, perm))
    else:
        L.append('无。')
    L.append('')
    L.append('## C 控制器覆盖率')
    L.append('')
    L.append('| 控制器 | 已用/总数 | 覆盖率 |')
    L.append('|---|---|---|')
    for cls, v in rows:
        L.append('| %s | %d/%d | %.1f%% |' % (cls, v['used'], v['total'],
                                              pct(v['used'], v['total'])))
    io.open(out, 'w', encoding='utf-8', newline='').write('\n'.join(L) + '\n')
    print('\nMarkdown 已写入:', out)
