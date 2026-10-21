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


def norm_path(p):
    """把路径参数归一化：前端 ${code} 与后端 {code} 视作同一接口"""
    p = re.sub(r'\$\{[^}]+\}', '{p}', p)
    p = re.sub(r'\{[^}]+\}', '{p}', p)
    return p


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
    """返回 {path: {'keys': set, 'literal': bool}}

    keys 只收集「字面量参数对象」里的键；literal 表示该路径存在可静态分析的调用。
    透传式（{ params } / { params: obj }）无法得知具体键，只跳过该次调用本身，
    不能因此把整条路径的检查都跳过——同一接口往往既有透传也有字面量调用。
    """
    out = {}
    for dirpath, _, files in os.walk(FE):
        if 'node_modules' in dirpath:
            continue
        for fn in files:
            if not fn.endswith(('.js', '.vue')):
                continue
            src = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
            for m in re.finditer(r"req\.get\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*\{", src):
                path = norm_path(m.group(1))
                slot = out.setdefault(path, {'keys': set(), 'literal': False})
                tail = src[m.end(): m.end() + 600]
                if re.match(r'\s*params\s*[,}]', tail) or \
                   re.match(r'\s*params\s*:\s*[A-Za-z_$][\w$]*\s*[,}]', tail):
                    continue
                pm = re.search(r'params:\s*\{([^}]*)\}', tail)
                if not pm:
                    continue
                for part in pm.group(1).split(','):
                    k = part.split(':')[0].strip()
                    if re.fullmatch(r'[A-Za-z_$][\w$]*', k):
                        slot['keys'].add(k)
                        slot['literal'] = True
    return out

def main():
    be = scan_backend()
    fe = scan_frontend()

    rows = []
    dead = []
    for full, params in be.items():
        api_path = norm_path(full.replace('/api/v1', ''))
        slot = fe.get(api_path) or {}
        used = slot.get('keys', set())
        missing = sorted(p for p in params if p not in used and p not in IGNORE)
        if not missing:
            continue
        rec = (len(missing), api_path, sorted(params), used, missing)
        # 前端从未调用过该接口 → 属于死接口/待开发，不是「漏接参数」
        (rows if used else dead).append(rec)

    rows.sort(reverse=True)
    dead.sort(reverse=True)
    print('后端 GET 接口 %d 个，前端有参数调用 %d 处' % (len(be), len(fe)))

    print('\n【可接】前端已调用、但漏传参数的接口：%d 个' % len(rows))
    if DETAIL:
        for n, path, supported, used, missing in rows:
            print('%-40s 缺 %d：%s' % (path, n, ', '.join(missing)))
            print('    后端支持: %s ｜ 前端已传: %s'
                  % (', '.join(supported), ', '.join(sorted(used)) or '(无)'))
    else:
        print('%-40s %s' % ('接口', '未接参数'))
        for n, path, supported, used, missing in rows:
            print('%-40s %s' % (path, ', '.join(missing)[:60]))

    print('\n【死接口】前端从未调用的接口：%d 个（不是漏接，先确认是否需要）' % len(dead))
    for n, path, supported, used, missing in dead:
        print('%-40s 支持参数: %s' % (path, ', '.join(supported)[:56]))

    total = sum(r[0] for r in rows)
    print('\n合计：可接 %d 个参数 / %d 个接口；死接口 %d 个' % (total, len(rows), len(dead)))

    # ---------- 反向检查：前端传了后端不认识的键（疑似拼写错误） ----------
    # 这类问题比「未接参数」更隐蔽：页面看着有筛选，实际参数被静默丢弃。
    # 已踩过三例：days/withinDays、contractStatus/status、todoStatus/status。
    print('\n' + '=' * 78)
    print('疑似拼写错误（前端传了后端没有的参数）')
    print('=' * 78)
    suspects = []
    for full, params in be.items():
        api_path = norm_path(full.replace('/api/v1', ''))
        slot = fe.get(api_path) or {}
        used = set(slot.get('keys', set()))
        if not used:
            continue      # 无可静态分析的字面量调用（全是透传）
        unknown = sorted(k for k in used if k not in params and k not in IGNORE)
        if unknown:
            suspects.append((api_path, unknown, sorted(params)))
    if not suspects:
        print('✔ 未发现')
    else:
        for path, unknown, supported in suspects:
            print('%-40s 前端多传: %s' % (path, ', '.join(unknown)))
            print('    后端只认: %s' % (', '.join(supported) or '(无)'))
    print('\n疑似拼写错误 %d 处' % len(suspects))
    # --strict：作为回归关卡时，存在前端传了后端不认的参数即失败。
    # 这类问题最隐蔽——筛选看着生效，其实参数被丢弃（已发生 6 次）。
    if '--strict' in sys.argv and suspects:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
