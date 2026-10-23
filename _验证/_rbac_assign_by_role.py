# -*- coding: utf-8 -*-
"""按角色性质自动分配权限；页面权限自动附带对应「查看」功能权限。

规则：
  ADMIN    全部页面 + 全部功能
  STAFF    全部页面 + 业务办理类功能（不含用户/权限/系统配置的删除）
  TENANT   租户自助页面 + 只读类功能
  ACCEPTOR 资格准入/合同页面 + 受理类动作
  REVIEWER 审核类页面 + 审核/审批动作
  FINANCE  账务页面 + 财务动作
  AUDITOR  全部页面（只读）+ 导出
  VIEWER   全部页面（只读）

另：任一角色拿到 page:<slug>:view 时，自动补上该页面对应资源的 view 功能权限
（slug→资源 的映射见 SLUG_RES）。
"""
import json
import sys
import urllib.request
import urllib.error

API = 'http://192.168.31.11:8080/api/v1'
DRY = '--dry' in sys.argv

# 页面 slug → 功能资源前缀（用于"有页面权限则自动有查看权限"）
SLUG_RES = {
    'contracts': ['biz:contract:view'],
    'contract-changes': ['biz:contract:view'],
    'exchanges': ['biz:exchange:view'],
    'terminations': ['biz:termination:view'],
    'applications': ['biz:application:view'],
    'allocations': ['biz:allocation:view'],
    'waitlist': ['biz:waitlist:view'],
    'persons': ['person:person:view', 'person:profile:view', 'person:verify:view'],
    'annual-reviews': ['person:profile:view'],
    'houses': ['asset:house:view'],
    'spaces': ['asset:space:view'],
    'house-calendar': ['asset:house:view'],
    'short-rent': ['asset:house:view'],
    'devices': ['asset:device:view'],
    'access': ['asset:grant:view'],
    'keyring': ['asset:keyring:view'],
    'grants': ['asset:grant:view'],
    'bills': ['fin:bill:view'],
    'deposits': ['fin:deposit:view'],
    'arrears': ['fin:arrear:view'],
    'subsidies': ['fin:subsidy:view'],
    'cashflow': ['fin:bill:view'],
    'fee-items': ['fin:feeItem:view'],
    'workorders': ['ops:workorder:view'],
    'complaints': ['ops:complaint:view'],
    'appeals': ['ops:appeal:view'],
    'visits': ['ops:visit:view'],
    'credits': ['ops:complaint:view'],
    'alerts': ['ops:alert:view'],
    'messages': ['msg:todo:view'],
    'todos': ['msg:todo:view'],
    'reports': ['rpt:report:view'],
    'orgs': ['iam:role:view'],
    'rbac': ['iam:user:view', 'iam:role:view', 'iam:perm:view'],
    'sys': ['sys:dict:view', 'sys:config:view', 'sys:audit:view'],
    'open': ['open:app:view'],
    'gov': ['gov:report:view'],
    'dashboard': [],
}

# 角色 → 页面 slug 列表（ALL 表示全部）
ROLE_PAGES = {
    'ADMIN': 'ALL',
    'STAFF': 'ALL',
    'AUDITOR': 'ALL',
    'VIEWER': 'ALL',
    'TENANT': ['bills', 'contracts', 'complaints', 'appeals', 'messages', 'todos', 'persons'],
    'ACCEPTOR': ['applications', 'waitlist', 'publicities', 'persons', 'annual-reviews',
                 'allocations', 'contracts'],
    'REVIEWER': ['applications', 'annual-reviews', 'persons', 'publicities'],
    'FINANCE': ['bills', 'deposits', 'arrears', 'subsidies', 'cashflow', 'reports', 'fee-items'],
}

# 角色 → 额外功能权限动作白名单（模块:资源:动作）
ROLE_EXTRA = {
    'ADMIN': 'ALL',
    'STAFF': ['biz:*:create', 'biz:*:update', 'biz:*:audit', 'biz:*:approve',
              'biz:*:sign', 'biz:*:renew', 'biz:*:terminate', 'biz:*:execute',
              'person:*:create', 'person:*:update', 'person:*:status', 'person:*:judge',
              'asset:*:create', 'asset:*:update', 'asset:*:grant', 'asset:*:revoke',
              'fin:*:create', 'fin:*:issue', 'fin:*:pay', 'fin:*:refund', 'fin:*:deduct',
              'ops:*:create', 'ops:*:handle', 'ops:*:assign', 'ops:*:close',
              'msg:*:read', 'msg:*:done', 'msg:*:create',
              'rpt:*:view', 'rpt:*:export'],
    'ACCEPTOR': ['biz:application:*', 'biz:waitlist:*', 'biz:allocation:view',
                 'biz:contract:view', 'biz:contract:create', 'person:*:view',
                 'person:person:create', 'person:person:update', 'ops:complaint:handle'],
    'REVIEWER': ['biz:application:audit', 'biz:application:approve',
                 'person:profile:judge', 'person:person:view', 'person:profile:view'],
    'FINANCE': ['fin:*:*', 'rpt:*:view', 'rpt:*:export', 'biz:contract:view',
                 'person:person:view', 'asset:house:view', 'biz:application:view'],
    'AUDITOR': ['rpt:*:export', 'sys:audit:export'],
    'VIEWER': [],
    'TENANT': ['fin:bill:view', 'fin:deposit:view', 'biz:contract:view',
                'asset:house:view', 'ops:workorder:view', 'ops:workorder:create',
                'person:person:view', 'biz:termination:create', 'biz:exchange:create',
                'biz:application:view', 'biz:application:create', 'biz:waitlist:view',
                'biz:annualReview:view', 'biz:publicity:view',
                'ops:complaint:create', 'ops:appeal:create', 'msg:todo:read'],
    'CONTRACT_CLERK': ['biz:contract:*', 'biz:application:view', 'biz:termination:view',
                       'asset:house:view', 'person:person:view', 'fin:bill:view'],
    'ASSET_CLERK': ['asset:*:*', 'biz:contract:view', 'biz:application:view',
                    'person:person:view', 'ops:workorder:view'],
    'SERVICE_CLERK': ['ops:*:*', 'msg:*:*', 'biz:contract:view', 'biz:application:view',
                      'person:person:view', 'asset:house:view', 'fin:bill:view'],
    'SYSTEM': ['open:*:*', 'sys:*:view', 'rpt:*:view'],
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
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP%d' % e.code}


def match(pattern, code):
    """支持 * 通配：biz:*:create / fin:*:*"""
    p, c = pattern.split(':'), code.split(':')
    if len(p) != len(c):
        return False
    return all(a == '*' or a == b for a, b in zip(p, c))


def main():
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    roles = call('/rbac/roles', token=token)['data']
    perms = call('/rbac/permissions', token=token)['data']
    by_code = {p['permCode']: p for p in perms}

    page_perms = [p for p in perms if p['permCode'].startswith('page:')]
    func_perms = [p for p in perms if not p['permCode'].startswith('page:')]
    print('页面权限 %d / 功能权限 %d' % (len(page_perms), len(func_perms)))

    for role in roles:
        code = role['roleCode']
        pages_rule = ROLE_PAGES.get(code)
        extra = ROLE_EXTRA.get(code, [])
        if pages_rule is None and not extra:
            continue   # 未定义规则的角色保持原状

        chosen = set()
        # 1) 页面权限
        if pages_rule == 'ALL':
            chosen.update(p['id'] for p in page_perms)
            slugs = None
        else:
            slugs = set(pages_rule or [])
            for p in page_perms:
                slug = p['permCode'].split(':')[1]
                if slug in slugs:
                    chosen.add(p['id'])

        # 2) 页面 → 自动带出查看权限
        auto_view = set()
        if pages_rule == 'ALL':
            auto_view.update(p['id'] for p in func_perms if p['permCode'].endswith(':view'))
        else:
            for slug in (slugs or []):
                for fc in SLUG_RES.get(slug, []):
                    if fc in by_code:
                        auto_view.add(by_code[fc]['id'])
        chosen |= auto_view

        # 3) 角色额外功能权限
        if extra == 'ALL':
            chosen.update(p['id'] for p in func_perms)
        else:
            for pat in extra:
                for p in func_perms:
                    if match(pat, p['permCode']):
                        chosen.add(p['id'])

        ids = sorted(chosen)
        if DRY:
            print('  [dry] %-9s -> %d 项（页面+查看 %d，其余功能 %d）'
                  % (code, len(ids), len(auto_view), len(ids) - len(auto_view)))
            continue
        r = call('/rbac/roles/%s/permissions' % role['id'], 'POST', {'ids': ids}, token)
        print('  %-9s 分配 %3d 项 -> %s' % (code, len(ids), r.get('code')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
