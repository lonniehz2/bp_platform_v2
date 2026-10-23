# -*- coding: utf-8 -*-
"""一键补全接口权限：生成缺失权限码 → 分配角色 → 补注解 → 精确去重。

规则与白名单统一来自 _perm_rules.py，避免生成端/注解端推导不一致。

用法：
  python _perm_sync.py            # 只统计
  python _perm_sync.py --apply    # 执行（建码 + 补注解）
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

from _perm_rules import (derive, is_public, perm_name, RES_CN, ACTION_CN)

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
APPLY = '--apply' in sys.argv


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP%d' % e.code}


def token():
    d = call('/auth/login', 'POST',
             {'tenantCode': TENANT, 'username': 'admin', 'password': 'admin123'})
    return d['data']['token']


def scan():
    """扫描所有控制器，返回 (待注解列表, 已注解数, 公开跳过数, 无法推导数)。"""
    todo, done, public, underivable = [], 0, 0, 0
    for dirpath, _, files in os.walk(JAVA):
        for fn in sorted(files):
            if not fn.endswith('Controller.java'):
                continue
            p = os.path.join(dirpath, fn)
            s = io.open(p, encoding='utf-8').read()
            m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', s)
            base = m.group(1) if m else ''
            lines = s.splitlines()
            for i, line in enumerate(lines):
                mm = re.search(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', line)
                if not mm:
                    continue
                kind, sub = mm.group(1), (mm.group(2) or '')
                full = (base.rstrip('/') + '/' + sub.lstrip('/')).rstrip('/') or base
                if is_public(full):
                    public += 1
                    continue
                has = False
                for back in range(i - 1, max(-1, i - 15), -1):
                    prev = lines[back]
                    if 'RequirePerm' in prev:
                        has = True
                        break
                    if ('Mapping' in prev and '@' in prev) or 'class ' in prev \
                            or prev.strip().startswith('}') or 'public ' in prev:
                        break
                # 注解也可能写在映射注解之后（方法签名之前），需向后再看
                if not has:
                    for fwd in range(i + 1, min(len(lines), i + 8)):
                        nxt = lines[fwd]
                        if 'RequirePerm' in nxt:
                            has = True
                            break
                        if 'public ' in nxt or 'private ' in nxt or 'protected ' in nxt \
                                or '(' in nxt and ')' in nxt:
                            break
                if has:
                    done += 1
                    continue
                d = derive(base, kind, sub)
                if not d:
                    underivable += 1
                    continue
                todo.append({'file': p, 'line': i, 'code': d[0], 'module': d[1],
                             'res': d[2], 'act': d[3], 'path': full})
    return todo, done, public, underivable


def annotate(items):
    by_file = {}
    for it in items:
        by_file.setdefault(it['file'], []).append(it)
    added = 0
    for p, its in by_file.items():
        lines = io.open(p, encoding='utf-8').read().splitlines(True)
        for it in sorted(its, key=lambda x: -x['line']):
            indent = re.match(r'\s*', lines[it['line']]).group(0)
            lines.insert(it['line'],
                         '%s@com.yundao.bp.iam.security.RequirePerm("%s")\n'
                         % (indent, it['code']))
            added += 1
        io.open(p, 'w', encoding='utf-8', newline='').write(''.join(lines))
    return added


def main():
    todo, done, public, underivable = scan()
    total = done + public + underivable + len(todo)
    print('接口总数        : %d' % total)
    print('已有注解        : %d' % done)
    print('公开白名单      : %d' % public)
    print('无法推导        : %d' % underivable)
    print('待补注解        : %d' % len(todo))
    covered = done + public
    print('当前有效覆盖    : %d (%.0f%%)' % (covered, covered * 100.0 / max(total, 1)))
    if not todo:
        print('\n无需补充')
        return 0
    if not APPLY:
        codes = sorted({x['code'] for x in todo})
        print('\n涉及权限码 %d 个（前 10）：' % len(codes))
        for c in codes[:10]:
            print('  ' + c)
        print('\n（dry-run；加 --apply 执行）')
        return 0

    t = token()
    perms = call('/rbac/permissions', token=t).get('data') or []
    exist = {p.get('permCode') for p in perms}
    needed = sorted({x['code'] for x in todo})
    created = 0
    for code in needed:
        if code in exist:
            continue
        module, res, act = code.split(':')
        body = {'permCode': code, 'permName': perm_name(res, act),
                'permType': 'API', 'module': module, 'resourceName': RES_CN.get(res, res),
                'actionName': ACTION_CN.get(act, act)}
        r = call('/rbac/permissions', 'POST', body, t)
        if r.get('code') == 'BP00000':
            created += 1
    print('\n新建权限码      : %d' % created)

    added = annotate(todo)
    print('补注解          : %d 处' % added)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
