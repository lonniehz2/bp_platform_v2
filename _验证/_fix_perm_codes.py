# -*- coding: utf-8 -*-
"""修正权限码推导：类路径只有模块段时，资源从方法子路径取。

问题：BillingController 类路径是 /api/v1/fin（只有模块），原先推导出 fin:fin:view；
正确应为 fin:bill:view（资源取自 @GetMapping("/bills")）。

处理：重写脚本自动添加的 FQ 注解（@com.yundao...RequirePerm），保留原有短注解。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

MODULES = {'biz', 'fin', 'asset', 'person', 'iam', 'sys', 'msg', 'ops', 'rpt', 'open', 'gov'}
METHOD_ACT = {'Get': 'view', 'Post': 'create', 'Put': 'update', 'Delete': 'delete'}
VERBS = ['approve', 'audit', 'sign', 'renew', 'terminate', 'change', 'transfer', 'execute',
         'verify', 'judge', 'assign', 'grant', 'revoke', 'reset', 'issue', 'cancel',
         'pay', 'refund', 'deduct', 'calc', 'dunning', 'handle', 'close', 'read', 'done',
         'record', 'submit', 'roll', 'recalc', 'batch', 'publish', 'status', 'export',
         'import', 'scan', 'sync', 'send', 'broadcast', 'run', 'freeze', 'unfreeze',
         'query', 'detail', 'list', 'create', 'update', 'delete', 'view']
RES_ALIAS = {
    'contracts': 'contract', 'contract-changes': 'contract', 'applications': 'application',
    'terminations': 'termination', 'exchanges': 'exchange', 'allocations': 'allocation',
    'waiting': 'waitlist', 'persons': 'person', 'guarantee-profiles': 'profile',
    'verify-records': 'verify', 'houses': 'house', 'spaces': 'space', 'devices': 'device',
    'keyring': 'keyring', 'grants': 'grant', 'grant-reconcile': 'grant', 'bills': 'bill',
    'payments': 'payment', 'deposits': 'deposit', 'arrears': 'arrear', 'subsidies': 'subsidy',
    'fee-items': 'feeItem', 'dunnings': 'arrear', 'cash-flows': 'bill', 'todos': 'todo',
    'workorders': 'workorder', 'alerts': 'alert', 'complaints': 'complaint',
    'appeals': 'appeal', 'visits': 'visit', 'users': 'user', 'roles': 'role',
    'permissions': 'perm', 'dicts': 'dict', 'configs': 'config', 'audit-logs': 'audit',
    'reports': 'report', 'apps': 'app', 'open': 'app', 'gov': 'report',
    'cohabitants': 'person', 'short-rent': 'house', 'house-calendar': 'house',
}


def segs(path):
    parts = [p for p in path.split('/') if p]
    if parts and parts[0] == 'api':
        parts = parts[2:]
    return [p for p in parts if not p.startswith('{')]


def derive(class_path, kind, sub):
    ss = segs(class_path)
    module = ss[0] if ss else ''
    res = ''
    if len(ss) > 1:
        res = RES_ALIAS.get(ss[1], ss[1])
    if not res:
        # 类路径只有模块：资源取自方法子路径
        ssub = segs(sub)
        if ssub:
            res = RES_ALIAS.get(ssub[0], ssub[0])
    act = METHOD_ACT.get(kind, 'view')
    low = sub.lower()
    for v in VERBS:
        if v in low:
            act = v
            break
    if not module or not res:
        return None
    return '%s:%s:%s' % (module, res, act)


def main():
    changed_files = 0
    changed_lines = 0
    for dirpath, _, files in os.walk(JAVA):
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            p = os.path.join(dirpath, fn)
            src = io.open(p, encoding='utf-8').read()
            m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', src)
            if not m:
                continue
            base = m.group(1)
            lines = src.splitlines(True)
            out = []
            n = 0
            for line in lines:
                mm = re.search(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', line)
                if mm and out and re.search(r'@com\.yundao\.bp\.iam\.security\.RequirePerm', out[-1]):
                    correct = derive(base, mm.group(1), mm.group(2) or '')
                    if correct:
                        cur = re.search(r'RequirePerm\("([^"]+)"\)', out[-1])
                        if cur and cur.group(1) != correct:
                            out[-1] = re.sub(r'RequirePerm\("[^"]+"\)',
                                             'RequirePerm("%s")' % correct, out[-1])
                            n += 1
                out.append(line)
            if n:
                io.open(p, 'w', encoding='utf-8', newline='').write(''.join(out))
                print('%s：修正 %d 处权限码' % (fn, n))
                changed_files += 1
                changed_lines += n
    print('合计修正 %d 处，涉及 %d 个文件' % (changed_lines, changed_files))


if __name__ == '__main__':
    main()
