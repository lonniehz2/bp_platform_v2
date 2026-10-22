# -*- coding: utf-8 -*-
"""给查询类接口补 @RequirePerm（写接口多数已有）。

策略（保守，避免误伤）：
  1. 只为「已存在权限码」的接口加注解——库里没有的码会让非管理员全部 403
  2. 权限码由「类级 @RequestMapping 路径 + 方法语义」推导：
       /api/v1/fin/bills  + @GetMapping  -> fin:bill:view
       /api/v1/fin/bills  + @PostMapping -> fin:bill:create
       ... + @PutMapping -> update / @DeleteMapping -> delete
       子路径 /{id}/approve -> <module>:<resource>:approve
  3. 已有 @RequirePerm 的方法跳过；未匹配到权限码的跳过并计入报告

用法：python _add_require_perm.py [--apply]   默认 dry-run
"""
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
API = 'http://192.168.31.11:8080/api/v1'
APPLY = '--apply' in sys.argv

METHOD_TO_ACT = {'Get': 'view', 'Post': 'create', 'Put': 'update', 'Delete': 'delete'}

# 动作 → 语义化权限动作（子路径里出现这些词时优先用它们）
VERB_HINTS = ['approve', 'audit', 'sign', 'renew', 'terminate', 'change', 'transfer',
              'execute', 'verify', 'judge', 'assign', 'grant', 'revoke', 'reset',
              'issue', 'cancel', 'pay', 'refund', 'deduct', 'calc', 'dunning',
              'handle', 'close', 'read', 'done', 'record', 'submit', 'roll', 'recalc',
              'batch', 'publish', 'status', 'export', 'import']

# 路径段 → 资源名归一（复数 / 业务别名）
RES_ALIAS = {
    'contracts': 'contract', 'contract-changes': 'contract', 'applications': 'application',
    'terminations': 'termination', 'exchanges': 'exchange', 'allocations': 'allocation',
    'waiting': 'waitlist', 'persons': 'person', 'guarantee-profiles': 'profile',
    'verify-records': 'verify', 'houses': 'house', 'spaces': 'space',
    'devices': 'device', 'keyring': 'keyring', 'grants': 'grant', 'grant-reconcile': 'grant',
    'bills': 'bill', 'payments': 'payment', 'deposits': 'deposit', 'arrears': 'arrear',
    'subsidies': 'subsidy', 'fee-items': 'feeItem', 'dunnings': 'arrear',
    'cash-flows': 'bill', 'todos': 'todo', 'workorders': 'workorder', 'alerts': 'alert',
    'complaints': 'complaint', 'appeals': 'appeal', 'visits': 'visit',
    'users': 'user', 'roles': 'role', 'permissions': 'perm', 'dicts': 'dict',
    'configs': 'config', 'audit-logs': 'audit', 'reports': 'report',
    'apps': 'app', 'open': 'app', 'gov': 'report',
}


def fetch_perm_codes():
    def call(path, method='GET', body=None, token=None):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(API + path, data=data, method=method)
        r.add_header('Content-Type', 'application/json')
        r.add_header('X-Tenant-Id', '350600')
        if token:
            r.add_header('Authorization', 'Bearer ' + token)
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    return {p['permCode'] for p in call('/rbac/permissions', token=token)['data']}


def segs(path):
    """拆出语义段：跳过 /api/v1 与 {param} 段"""
    parts = [p for p in path.split('/') if p]
    if parts and parts[0] == 'api':
        parts = parts[2:]
    return [p for p in parts if not p.startswith('{')]


def module_of(path):
    ss = segs(path)
    return ss[0] if ss else ''


def resource_of(path):
    ss = segs(path)
    seg = ss[1] if len(ss) > 1 else (ss[0] if ss else '')
    return RES_ALIAS.get(seg, seg)


def main():
    codes = fetch_perm_codes()
    print('库中权限码 %d 个' % len(codes))

    added = skipped_have = skipped_nocode = 0
    touched_files = 0
    report = []

    for dirpath, _, files in os.walk(JAVA):
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            path = os.path.join(dirpath, fn)
            src = io.open(path, encoding='utf-8').read()
            if '@RequirePerm' not in src and '@RequestMapping' not in src:
                continue

            m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', src)
            if not m:
                continue
            base = m.group(1)
            module = module_of(base)
            res = resource_of(base)
            if not module or not res:
                continue

            lines = src.splitlines(True)
            out = []
            changed = 0
            pending_annotation = []      # 待插入的注解位置

            for i, line in enumerate(lines):
                # 记录最近出现的映射注解与其方法类型
                mm = re.search(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', line)
                if mm:
                    kind, sub = mm.group(1), (mm.group(2) or '')
                    # 找该方法前 3 行是否已有 RequirePerm
                    ctx = ''.join(lines[max(0, i - 8):i])
                    has_perm = '@RequirePerm' in ctx
                    if has_perm:
                        skipped_have += 1
                        out.append(line)
                        continue
                    act = METHOD_TO_ACT.get(kind, 'view')
                    low = sub.lower()
                    for v in VERB_HINTS:
                        if v in low:
                            act = v
                            break
                    code = '%s:%s:%s' % (module, res, act)
                    alt = '%s:%s:view' % (module, res)
                    use = code if code in codes else (alt if alt in codes else None)
                    if not use:
                        skipped_nocode += 1
                        report.append('%s %s %s -> 无匹配权限码(%s)' % (fn, kind, sub or '/', code))
                        out.append(line)
                        continue
                    # 已有其他注解行时，插在同级注解之前
                    out.append('    @com.yundao.bp.iam.security.RequirePerm("%s")\n' % use)
                    out.append(line)
                    added += 1
                    changed += 1
                    continue
                out.append(line)

            if changed:
                touched_files += 1
                if APPLY:
                    io.open(path, 'w', encoding='utf-8', newline='').write(''.join(out))

    print('可新增注解 %d 处，涉及 %d 个文件' % (added, touched_files))
    print('已有注解跳过 %d 处，无匹配权限码跳过 %d 处' % (skipped_have, skipped_nocode))
    if report:
        print('\n无匹配权限码样例（前 10 条）：')
        for line in report[:10]:
            print('  ' + line)
    if not APPLY:
        print('\n（dry-run；加 --apply 写入）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
