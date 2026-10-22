# -*- coding: utf-8 -*-
"""按岗位拆分角色权限：新增合同经办 / 房源管理 / 服务协同，并收窄「工作人员」。

设计原则：
  岗位角色 = 该岗位需要的页面 + 动作，不越界到审核/审批/退款等高权动作
  STAFF   = 通用业务员：全页面只读 + 常规办理（新建/编辑/处理/标记），不含审批类
"""
import json
import sys
import urllib.request
import urllib.error

API = 'http://192.168.31.11:8080/api/v1'
DRY = '--dry' in sys.argv

NEW_ROLES = [
    ('CONTRACT_CLERK', '合同经办', 'ORG'),
    ('ASSET_CLERK', '房源管理', 'ORG'),
    ('SERVICE_CLERK', '服务协同', 'ORG'),
]

ROLE_PAGES = {
    'STAFF': 'ALL',   # 通用业务员：全部页面只读 + 常规办理
    'CONTRACT_CLERK': ['contracts', 'contract-changes', 'exchanges', 'terminations',
                       'persons', 'applications'],
    'ASSET_CLERK': ['houses', 'spaces', 'house-calendar', 'short-rent', 'devices',
                    'access', 'keyring', 'grants', 'workorders'],
    'SERVICE_CLERK': ['workorders', 'complaints', 'appeals', 'visits', 'alerts',
                      'credits', 'messages', 'todos'],
}

ROLE_EXTRA = {
    'CONTRACT_CLERK': ['biz:contract:*', 'biz:exchange:*', 'biz:termination:*',
                       'biz:application:view', 'person:person:view', 'person:profile:view',
                       'msg:todo:view', 'msg:todo:read', 'rpt:report:view'],
    'ASSET_CLERK': ['asset:*:*', 'biz:contract:view', 'ops:workorder:*', 'ops:visit:*',
                    'person:person:view', 'msg:todo:view', 'msg:todo:read'],
    'SERVICE_CLERK': ['ops:complaint:*', 'ops:appeal:*', 'ops:visit:*', 'ops:alert:*',
                      'ops:workorder:*', 'msg:*:*', 'person:person:view',
                      'asset:house:view', 'biz:contract:view'],
    # 收窄：只保留常规办理，去掉审核/审批/终止/退款/撤销等高权动作
    'STAFF': ['biz:*:view', 'biz:*:create', 'biz:*:update', 'biz:*:change',
              'person:*:view', 'person:person:create', 'person:person:update',
              'person:profile:create', 'person:profile:update',
              'asset:*:view', 'asset:*:create', 'asset:*:update', 'asset:*:grant',
              'fin:*:view', 'fin:bill:create', 'fin:payment:create',
              'ops:*:view', 'ops:*:create', 'ops:*:handle', 'ops:*:record',
              'msg:*:*', 'rpt:*:view', 'sys:*:view', 'iam:user:view', 'iam:role:view'],
}


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return {'code': 'HTTP%d' % e.code}


def match(pattern, code):
    p, c = pattern.split(':'), code.split(':')
    if len(p) != len(c):
        return False
    return all(a == '*' or a == b for a, b in zip(p, c))


def main():
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    roles = {r['roleCode']: r for r in call('/rbac/roles', token=token)['data']}
    perms = call('/rbac/permissions', token=token)['data']
    by_code = {p['permCode']: p for p in perms}
    page_perms = [p for p in perms if p['permCode'].startswith('page:')]
    func_perms = [p for p in perms if not p['permCode'].startswith('page:')]

    # 1) 建新角色
    for code, name, scope in NEW_ROLES:
        if code in roles:
            print('角色已存在：%s' % code)
            continue
        if DRY:
            print('[dry] 创建角色 %s(%s)' % (code, name))
            continue
        r = call('/rbac/roles', 'POST',
                 {'roleCode': code, 'roleName': name, 'dataScope': scope}, token)
        print('创建角色 %s(%s) -> %s' % (code, name, r.get('code')))
    if not DRY:
        roles = {r['roleCode']: r for r in call('/rbac/roles', token=token)['data']}

    # 2) 分配
    for code, slugs in ROLE_PAGES.items():
        if code not in roles:
            print('跳过（角色不存在）：%s' % code)
            continue
        chosen = set()
        if slugs == 'ALL':
            chosen.update(p['id'] for p in page_perms)
            slug_set = set()
        else:
            slug_set = set(slugs)
        for p in page_perms:
            if p['permCode'].split(':')[1] in slug_set:
                chosen.add(p['id'])
        for pat in ROLE_EXTRA.get(code, []):
            for p in func_perms:
                if match(pat, p['permCode']):
                    chosen.add(p['id'])
        # 有页面权限则至少能看：自动补该模块 view
        ids = sorted(chosen)
        if DRY:
            print('  [dry] %-15s -> %d 项' % (code, len(ids)))
            continue
        r = call('/rbac/roles/%s/permissions' % roles[code]['id'], 'POST', {'ids': ids}, token)
        print('  %-15s 分配 %3d 项 -> %s' % (code, len(ids), r.get('code')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
