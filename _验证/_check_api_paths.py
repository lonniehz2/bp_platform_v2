# -*- coding: utf-8 -*-
"""前后端接口路径一致性核对（静态分析，无需运行环境）

用法：
    python _check_api_paths.py            # 打印报告
    python _check_api_paths.py --strict   # 存在不匹配时退出码 1（供 CI 使用）

原理：
    后端：解析每个 Controller 的 @RequestMapping 根路径 + 方法级
          @GetMapping/@PostMapping/... 子路径，拼成完整路径并归一化
          （{id}、${x} 统一成 {}，忽略查询串）
    前端：解析 src/api/modules.js 与各 .vue 内的 req.get/post/... 调用，
          补上 baseURL 前缀 /api/v1

输出：
    ❌ 前端路径后端不存在   → 真实 404 风险，必须修
    ⚠️ HTTP 方法不匹配      → 路径对但方法错
    ℹ️ 后端接口未被前端调用 → 信息性（可能不需要前端）
"""
import io
import os
import re
import sys

WORK = r'D:\Work\业务平台开发'
JAVA = os.path.join(WORK, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
FE = os.path.join(WORK, 'frontend', 'src')
API_PREFIX = '/api/v1'

STRICT = '--strict' in sys.argv

# 已知缺口：后端尚未提供对应接口（非前端写错），单独统计不计为错误
KNOWN_GAP = {
    ('GET', '/api/v1/devices'),                      # 无设备列表接口
    ('POST', '/api/v1/publicities/{}/finish'),        # 公示结束动作路径待确认
    ('POST', '/api/v1/visits/{}/approve'),            # 已改为 /report，此行保留兼容
}


def norm_path(p):
    """归一化：{id} / ${id} / {a}/{b} → {} ; 去查询串与尾斜杠。"""
    if p is None:
        return ''
    p = p.split('?')[0].strip()
    p = re.sub(r'\$\{[^}]+\}', '{}', p)      # 前端模板串
    p = re.sub(r'\{[^}]+\}', '{}', p)        # 后端占位符
    p = re.sub(r'/+', '/', p)
    if len(p) > 1 and p.endswith('/'):
        p = p[:-1]
    return p


# ==================== 后端 ====================
backend = {}   # norm_path -> set(methods)  以及来源文件
backend_src = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        fp = os.path.join(root, f)
        s = io.open(fp, encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not m:
            continue
        base = m.group(1)
        # 方法级映射（含无路径的 @GetMapping）
        # 兼容两种写法：@GetMapping 与 @GetMapping("/x")，以及 @GetMapping(value="/x")
        # 早期版本只匹配带括号的，导致大量「无括号映射」被漏掉，产生误报
        for mm in re.finditer(
                r'@(Get|Post|Put|Delete|Patch)Mapping'
                r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?', s):
            verb = mm.group(1).upper()
            sub = mm.group(2) or ''
            full = norm_path(base + ('/' + sub if sub else ''))
            backend.setdefault(full, set()).add(verb)
            backend_src[full] = os.path.basename(fp)

# ==================== 前端 ====================
fe_calls = []   # (method, path, 来源)
files = []
for root, _, fs in os.walk(FE):
    for f in fs:
        if f.endswith(('.js', '.vue')):
            files.append(os.path.join(root, f))

CALL_RE = re.compile(
    r'req\.(get|post|put|delete)\(\s*[`\'"](/[^`\'"]*)[`\'"]', re.I)
TPL_RE = re.compile(r'`(/[^`]*)`')

for fp in files:
    s = io.open(fp, encoding='utf-8').read()
    fname = os.path.relpath(fp, FE)
    for m in CALL_RE.finditer(s):
        verb = m.group(1).upper()
        raw = m.group(2)
        if raw.startswith('/api/'):
            full = norm_path(raw)
        else:
            full = norm_path(API_PREFIX + raw)
        fe_calls.append((verb, full, fname))

# ==================== 比对 ====================
missing = []      # 前端有、后端无（前端写错）
known = []        # 已知缺口（后端未提供）
method_bad = []   # 路径在、方法不匹配
for verb, full, src in fe_calls:
    if full in backend:
        if verb not in backend[full] and 'GET' not in backend[full] | {verb}:
            if verb not in backend[full]:
                method_bad.append((verb, full, sorted(backend[full]), src))
    elif (verb, full) in KNOWN_GAP:
        known.append((verb, full, src))
    else:
        missing.append((verb, full, src))

called = {c[1] for c in fe_calls}
unused = sorted(p for p in backend if p not in called)

print('=' * 84)
print(' 前后端接口路径核对')
print('=' * 84)
print('  后端接口  %d 个（%d 个 Controller 文件）'
      % (len(backend), len({v for v in backend_src.values()})))
print('  前端调用  %d 处（%d 个源文件）' % (len(fe_calls), len(files)))
print()

if missing:
    print('❌ 前端调用但后端不存在（%d 处）—— 会 404，必须修：' % len(missing))
    for verb, full, src in sorted(set(missing)):
        print('   %-6s %-46s %s' % (verb, full, src))
else:
    print('✅ 前端所有调用路径在后端均存在')
print()

if method_bad:
    print('⚠️ 路径存在但 HTTP 方法不匹配（%d 处）：' % len(method_bad))
    for verb, full, allow, src in sorted(set(
            (v, f, tuple(a), s) for v, f, a, s in method_bad)):
        print('   %-6s %-40s 后端支持 %s  (%s)'
              % (verb, full, '/'.join(allow), src))
    print()

if known:
    print('🟡 已知缺口（后端尚未提供，非前端错误）：%d 处' % len(known))
    for verb, full, src in sorted(set(known)):
        print('   %-6s %-46s %s' % (verb, full, src))
    print()

if unused:
    print('ℹ️ 后端接口未被前端调用（%d 个，仅供参考）：' % len(unused))
    for p in unused[:40]:
        print('   %-52s %s' % (p, '/'.join(sorted(backend[p]))))
    if len(unused) > 40:
        print('   …（其余 %d 个略）' % (len(unused) - 40))
    print()

print('-' * 84)
ok = not missing and not method_bad
print(' 结论：%s' % ('通过' if ok else
                    '发现 %d 处必须修正的问题' % (len(missing) + len(method_bad))))
print('-' * 84)

if STRICT and not ok:
    sys.exit(1)
