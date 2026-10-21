# -*- coding: utf-8 -*-
"""量化：SPA 是否覆盖后端全部功能（读 vs 写）"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FE = r'D:\Work\业务平台开发\frontend\src'


def norm(p):
    p = (p or '').split('?')[0]
    p = re.sub(r'\$\{[^}]+\}', '{}', p)
    p = re.sub(r'\{[^}]+\}', '{}', p)
    p = re.sub(r'/+', '/', p)
    return p.rstrip('/') if len(p) > 1 else p


# 后端
backend = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not m:
            continue
        base = m.group(1)
        for mm in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping'
                              r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?', s):
            verb, sub = mm.group(1).upper(), mm.group(2) or ''
            full = norm(base + ('/' + sub if sub else ''))
            backend.setdefault((full, verb), os.path.basename(f))

# 前端
fe = set()
for root, _, files in os.walk(FE):
    for f in files:
        if not f.endswith(('.js', '.vue')):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        for mm in re.finditer(r'req\.(get|post|put|delete)\(\s*[`\'"](/[^`\'"]*)', s):
            verb, raw = mm.group(1).upper(), mm.group(2)
            full = norm(raw if raw.startswith('/api/') else '/api/v1' + raw)
            fe.add((full, verb))

reads = [k for k in backend if k[1] == 'GET']
writes = [k for k in backend if k[1] != 'GET']
r_cov = [k for k in reads if k in fe]
w_cov = [k for k in writes if k in fe]

print('=' * 74)
print(' SPA 功能覆盖度（按读/写拆分）')
print('=' * 74)
print('  后端接口总计      %4d' % len(backend))
print('    其中查询(GET)   %4d' % len(reads))
print('    其中写操作       %4d  (POST/PUT/DELETE)' % len(writes))
print()
print('  前端调用点        %4d' % len(fe))
print('    覆盖查询接口     %4d  → %.1f%%' % (len(r_cov), len(r_cov) * 100.0 / len(reads)))
print('    覆盖写操作接口   %4d  → %.1f%%' % (len(w_cov), len(w_cov) * 100.0 / len(writes)))
print()

miss_w = sorted(set(writes) - fe)
print('  未被前端调用的写操作：%d 个（这些功能在 UI 上做不到）' % len(miss_w))
by_mod = {}
for full, verb in miss_w:
    mod = full.split('/')[3] if full.count('/') > 3 else 'root'
    by_mod.setdefault(mod, []).append('%s %s' % (verb, full))
for mod in sorted(by_mod, key=lambda m: -len(by_mod[m])):
    print('    %-16s %2d 个' % (mod, len(by_mod[mod])))
