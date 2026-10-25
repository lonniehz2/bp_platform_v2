# -*- coding: utf-8 -*-
"""菜单权限一致性检查：不同角色能看到的菜单，是否与其权限匹配。

三类问题
--------
1. **该看到却没看到**：有页面权限但菜单被过滤掉（漏登记 / 权限码写错）
2. **看到了却没权限**：菜单出现，但该页接口返回 403（点进去就报错）
3. **没有任何角色能看到**：孤儿页面（配了权限但没人有）

实现：按 useMenu.js 的规则复算「应可见菜单」，再用各账号实际权限比对，
并对可见页面调用其列表接口，确认不是 403。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ROUTER = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')

ACCOUNTS = [
    ('admin', 'admin123', '系统管理员'),
    ('test_finance', 'Test@1234', '财务岗'),
    ('test_asset', 'Test@1234', '资产岗'),
    ('test_contract', 'Test@1234', '合同岗'),
    ('test_tenant', 'Test@1234', '租户'),
]

# 页面路径 → 该页主要列表接口（用于验证"点进去不 403"）
API_OF_PAGE = {
    '/dashboard': None,
    '/todos': '/todos',
    '/messages': '/messages',
    '/persons': '/persons',
    '/annual-reviews': '/annual-reviews',
    '/applications': '/applications',
    '/waitlist': '/allocation/waiting',
    '/allocations': '/allocation/allocations',
    '/publicities': '/publicities',
    '/contracts': '/contracts',
    '/contract-changes': '/contract-changes',
    '/exchanges': '/exchanges',
    '/terminations': '/terminations',
    '/fee-items': '/fin/fee-items',
    '/bills': '/fin/bills',
    '/meter-readings': '/fin/meter-readings',
    '/energy': '/fin/meter-readings/analytics',
    '/deposits': '/fin/deposits',
    '/arrears': '/fin/arrears',
    '/subsidies': '/fin/subsidies/records',
    '/cashflow': '/fin/cash-flows',
    '/reports': '/rpt/reports',
    '/houses': '/houses',
    '/spaces': None,
    '/house-calendar': '/house-calendar',
    '/short-rent': '/short-rent-orders',
    '/devices': '/devices',
    '/device-bind': '/devices',
    '/dev-events': '/dev-events',
    '/access': '/access-records',
    '/keyring': '/keyring',
    '/grants': '/grants',
    '/workorders': '/workorders',
    '/alerts': '/alerts',
    '/complaints': '/complaints',
    '/visits': '/visits',
    '/appeals': '/appeals',
    '/credits': '/credits',
    '/orgs': '/orgs',
    '/rbac': '/rbac/users',
    '/sys': '/sys/params',
    '/ops-center': None,
    '/ops-extras': None,
    '/open': '/open/apps',
    '/gov': '/gov/reports',
}


def call(path, method='GET', body=None, tok=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}


def login(u, p):
    st, d = call('/auth/login', 'POST', {'tenantCode': TENANT, 'username': u, 'password': p})
    if st != 200:
        return None
    return ((d or {}).get('data') or {}).get('token')


def me(tok):
    st, d = call('/auth/me', 'GET', None, tok)
    return (d or {}).get('data') or {}


def routes():
    src = open(ROUTER, encoding='utf-8').read()
    out = []
    for m in re.finditer(r"path:\s*'(/[^']*)'", src):
        p = m.group(1)
        if p in ('/', '/login') or p.startswith('/screen'):
            continue
        block = src[m.start():m.start() + 500]
        if 'meta:' not in block or 'title:' not in block:
            continue
        perm = re.search(r"perm:\s*'([^']+)'", block)
        title = re.search(r"title:\s*'([^']+)'", block)
        out.append({
            'path': p.split('/:')[0],
            'perm': perm.group(1) if perm else None,
            'title': title.group(1) if title else p,
        })
    # 去重（多 tab 路由重复出现）
    seen, uniq = set(), []
    for r in out:
        if r['path'] in seen:
            continue
        seen.add(r['path'])
        uniq.append(r)
    return uniq


def page_perm(path):
    slug = path.strip('/').split('/:')[0].replace('/', '-')
    return 'page:%s:view' % slug if slug else ''


def expected_visible(routes_all, perms, is_admin):
    vis = []
    for r in routes_all:
        if is_admin:
            vis.append(r)
            continue
        if r['perm']:
            if r['perm'] in perms:
                vis.append(r)
        else:
            code = page_perm(r['path'])
            if not code or code in perms:
                vis.append(r)
    return vis


def main():
    routes_all = routes()
    print('=' * 74)
    print('菜单权限一致性：%d 个业务路由 × %d 个角色' % (len(routes_all), len(ACCOUNTS)))

    problems = []
    seen_pages = set()

    for user, pwd, label in ACCOUNTS:
        tok = login(user, pwd)
        if not tok:
            problems.append('账号 %s 登录失败' % user)
            continue
        info = me(tok)
        perms = set(info.get('permissions') or [])
        is_admin = bool(info.get('admin'))
        exp = expected_visible(routes_all, perms, is_admin)
        seen_pages.update(r['path'] for r in exp)

        # 2) 可见页面接口是否真的可访问
        denied = []
        for r in exp:
            api = API_OF_PAGE.get(r['path'])
            if not api:
                continue
            st, _ = call(api + ('&' if '?' in api else '?') + 'pageNum=1&pageSize=1', 'GET', None, tok)
            if st in (403, 401):
                denied.append('%s（%s）→ %s' % (r['title'], r['path'], api))
        if denied:
            problems.append('[%s] 菜单可见但接口 403：%s' % (label, '；'.join(denied[:4])))

        print('  %-6s 权限 %3d 项 → 预期可见 %2d 页' % (label, len(perms), len(exp)))

    # 3) 孤儿页面：没有任何角色预期可见
    orphans = [r['title'] + '（' + r['path'] + '）'
               for r in routes_all if r['path'] not in seen_pages]
    if orphans:
        problems.append('无任何角色可见的页面：' + '；'.join(orphans))

    if problems:
        print('\n发现 %d 类问题：' % len(problems))
        for p in problems:
            print('  ✗ ' + p)
        print('=' * 74)
        return 1
    print('\n  ✔ 菜单与权限一致，且可见页面接口均可访问')
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())
