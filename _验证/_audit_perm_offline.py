# -*- coding: utf-8 -*-
"""离线审计：不依赖 API/数据库，静态统计权限注解覆盖率与缺口分布。

用于网络不可达时继续推进分析；修复推导规则后可直接看预期收益。
"""
import os
import re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

MODULES = {'biz', 'fin', 'asset', 'person', 'iam', 'sys', 'msg', 'ops', 'rpt', 'open', 'gov'}
RES_MODULE = {
    'contract': 'biz', 'application': 'biz', 'termination': 'biz', 'exchange': 'biz',
    'allocation': 'biz', 'waitlist': 'biz', 'person': 'person', 'profile': 'person',
    'verify': 'person', 'house': 'asset', 'space': 'asset', 'device': 'asset',
    'grant': 'asset', 'keyring': 'asset', 'bill': 'fin', 'payment': 'fin',
    'deposit': 'fin', 'arrear': 'fin', 'subsidy': 'fin', 'feeItem': 'fin',
    'todo': 'msg', 'workorder': 'ops', 'alert': 'ops', 'complaint': 'ops',
    'appeal': 'ops', 'visit': 'ops', 'user': 'iam', 'role': 'iam', 'perm': 'iam',
    'dict': 'sys', 'config': 'sys', 'audit': 'sys', 'report': 'rpt', 'app': 'open',
}
RES_ALIAS = {
    'contracts': 'contract', 'contract-changes': 'contract', 'applications': 'application',
    'terminations': 'termination', 'exchanges': 'exchange', 'allocations': 'allocation',
    'houses': 'house', 'spaces': 'space', 'devices': 'device', 'persons': 'person',
    'bills': 'bill', 'payments': 'payment', 'deposits': 'deposit', 'arrears': 'arrear',
    'subsidies': 'subsidy', 'fee-items': 'feeItem', 'workorders': 'workorder',
    'complaints': 'complaint', 'appeals': 'appeal', 'visits': 'visit',
    'users': 'user', 'roles': 'role', 'permissions': 'perm', 'orgs': 'org',
}
METHOD_ACT = {'Get': 'view', 'Post': 'create', 'Put': 'update', 'Delete': 'delete'}

total = annotated = 0
derived = Counter()
missing_by_module = Counter()
unmapped = []

for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        p = os.path.join(dirpath, fn)
        s = open(p, encoding='utf-8', errors='replace').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', s)
        base = m.group(1) if m else ''
        parts = [x for x in base.split('/') if x and x != 'api' and not x.startswith('v')
                 and not x.startswith('{')]
        module = parts[0] if parts else ''
        res = RES_ALIAS.get(parts[1], parts[1]) if len(parts) > 1 else \
            RES_ALIAS.get(parts[0], parts[0]) if parts else ''
        if module not in MODULES:
            module = RES_MODULE.get(res, module)
        if not module or not res:
            unmapped.append(fn)

        lines = s.splitlines()
        for i, line in enumerate(lines):
            mm = re.search(r'@(Get|Post|Put|Delete)Mapping', line)
            if not mm:
                continue
            total += 1
            # 同一方法块内向前找注解
            has = False
            for back in range(i - 1, max(-1, i - 15), -1):
                prev = lines[back]
                if 'RequirePerm' in prev:
                    has = True
                    break
                if ('Mapping' in prev and '@' in prev) or 'class ' in prev \
                        or prev.strip().startswith('}') or 'public ' in prev:
                    break
            if has:
                annotated += 1
            else:
                act = METHOD_ACT.get(mm.group(1), 'view')
                code = '%s:%s:%s' % (module, res, act)
                derived[code] += 1
                missing_by_module[module] += 1

print('接口总数      : %d' % total)
print('已加注解      : %d (%.0f%%)' % (annotated, annotated * 100.0 / max(total, 1)))
print('未加注解      : %d' % (total - annotated))
print('\n未覆盖接口按模块分布：')
for mod, n in missing_by_module.most_common():
    print('  %-8s %d' % (mod or '(空)', n))
print('\n推导出的权限码种类：%d 个（前 15）' % len(derived))
for code, n in derived.most_common(15):
    print('  %-28s %d 个接口' % (code, n))
if unmapped:
    print('\n无法推导模块的控制器：%s' % ', '.join(sorted(set(unmapped))))
