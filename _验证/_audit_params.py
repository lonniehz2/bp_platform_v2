# -*- coding: utf-8 -*-
"""参数接线审计：找出「后端支持、前端从未传」的查询参数

背景：多轮排查发现「功能缺失」大多是前端没接后端已有参数，而非后端没实现。
这个脚本把差异一次性列出来，避免逐页翻查。

做法：
  1. 扫后端所有 Controller：类级 @RequestMapping 前缀 + @GetMapping 路径 + @RequestParam 名称
  2. 扫前端所有 req.get('/path', { params: {...} })：路径 → 实际传的参数名
  3. 取差集（后端有、前端没有），按缺失数量排序

用法：
  python _audit_params.py            # 汇总
  python _audit_params.py --detail   # 逐条列出
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java')
FE = os.path.join(ROOT, 'frontend', 'src')

DETAIL = '--detail' in sys.argv

# 分页/排序这类通用参数不算「缺失能力」
IGNORE = {'pageNum', 'pageSize', 'ids', 'id'}


def scan_backend():
    """返回 {完整路径: set(参数名)}"""
    out = {}
    for dirpath, _, files in os.walk(JAVA):
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            src = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
            m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', src)
            prefix = m.group(1) if m else ''
            for g in re.finditer(r'@GetMapping\("?([^")\n]*)"?\)', src):
                path = g.group(1).strip()
                if not path.startswith('/'):
                    path = '/' + path if path else ''
                full = prefix + path
                # 只在「本方法的签名」里找 @RequestParam：
                # 从 public 到第一个 { 之间。用固定窗口会把下一个方法的参数也算进来，
                # 导致详情接口（/xxx/{id}）被误报成支持列表参数。
                pub = src.find('public ', g.end())
                if pub == -1:
                    continue
                brace = src.find('{', pub)
                sig = src[pub: brace if brace != -1 else pub + 800]
                params = re.findall(
                    r'@RequestParam\([^)]*\)\s*(?:final\s+)?[\w<>.\[\]]+\s+(\w+)', sig)
                if params:
                    out.setdefault(full, set()).update(params)
    return out


def scan_frontend():
    """返回 {path: set(参数名)}；透传式调用（{ params } / { params: 变量 }）记为 '*'"""
    out = {}
    for dirpath, _, files in os.walk(FE):
        if 'node_modules' in dirpath:
            continue
        for fn in files:
            if not fn.endswith(('.js', '.vue')):
                continue
            src = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
            for m in re.finditer(r"req\.get\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*\{", src):
                path = m.group(1)
                tail = src[m.end(): m.end() + 600]
                # 透传式：{ params } 或 { params: p } —— 具体键由调用方决定，视为已接线
                if re.match(r'\s*params\s*[,}]', tail) or \
                   re.match(r'\s*params\s*:\s*[A-Za-z_$][\w$]*\s*[,}]', tail):
                    out.setdefault(path, set()).add('*')
                    continue
                pm = re.search(r'params:\s*\{([^}]*)\}', tail)
                keys = set()
                if pm:
                    # 兼容 { keyword: x } 与简写 { group } 两种写法
                    for part in pm.group(1).split(','):
                        k = part.split(':')[0].strip()
                        if re.fullmatch(r'[A-Za-z_$][\w$]*', k):
                            keys.add(k)
                out.setdefault(path, set()).update(keys)
    return out


def main():
    be = scan_backend()
    fe = scan_frontend()

    rows = []
    for full, params in be.items():
        api_path = full.replace('/api/v1', '')
        used = fe.get(api_path, set())
        if '*' in used:
            continue          # 透传式调用：页面自行决定参数，不算缺失
        missing = sorted(p for p in params if p not in used and p not in IGNORE)
        if missing:
            rows.append((len(missing), api_path, sorted(params), used, missing))

    rows.sort(reverse=True)
    print('后端 GET 接口 %d 个，前端有参数调用 %d 处' % (len(be), len(fe)))
    print('存在「后端支持但前端未传」参数的接口：%d 个\n' % len(rows))

    if DETAIL:
        for n, path, supported, used, missing in rows:
            print('%-42s 缺 %d：%s' % (path, n, ', '.join(missing)))
            print('    后端支持: %s' % ', '.join(supported))
            print('    前端已传: %s' % (', '.join(sorted(used)) or '(无)'))
    else:
        print('%-42s %s' % ('接口', '未接参数'))
        for n, path, supported, used, missing in rows[:40]:
            print('%-42s %s' % (path, ', '.join(missing)[:70]))

    total = sum(r[0] for r in rows)
    print('\n合计 %d 个未接参数，涉及 %d 个接口' % (total, len(rows)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
