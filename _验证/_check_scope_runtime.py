# -*- coding: utf-8 -*-
"""运行时数据范围校验：用受限账号实际请求列表接口，对比管理员返回量。

为什么需要
----------
静态扫描只能确认「有没有调用范围过滤」，无法确认「过滤列写对了没」。
本脚本用 SELF 档账号（租户）实际调用，若返回条数与管理员**完全相同且不为 0**，
说明该接口很可能没真正限权（漏调用，或过滤列写错）。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

HOST = 'http://192.168.31.11:8080'
BASE = HOST + '/api/v1'
TENANT = '350600'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CTRL = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# 公开/配置类：允许受限账号看到全量
PUBLIC = ('/publicities', '/regions', '/fee-items', '/sys/', '/rbac/', '/dev-events/stats',
          '/open/', '/gov/', '/dashboard', '/messages', '/todos', '/meta/')

# 需要登录但共享的基础数据
IGNORE_CLASSES = {'SysRegionController', 'SysDictController', 'SysParamController',
                  'PermissionController', 'RoleController', 'MenuController'}


def call(path, tok=None, body=None, method='GET'):
    data = json.dumps(body).encode() if body is not None else None
    url = HOST + path if path.startswith('/api/') else BASE + path
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}


def login(user, pwd):
    st, d = call('/auth/login', body={'tenantCode': TENANT, 'username': user,
                                      'password': pwd}, method='POST')
    return ((d or {}).get('data') or {}).get('token')


def discover():
    """扫描控制器，找出返回 PageResult 的 GET 列表接口。"""
    out = []
    for dirpath, _d, files in os.walk(CTRL):
        if not dirpath.replace('\\', '/').endswith('controller'):
            continue
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            cls = fn[:-5]
            if cls in IGNORE_CLASSES:
                continue
            src = open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
            base = re.search(r'@RequestMapping\("([^"]+)"\)', src)
            prefix = base.group(1) if base else ''
            for m in re.finditer(r'@GetMapping\("([^"]*)"\)', src):
                tail = m.group(1)
                seg = src[m.end():m.end() + 600]
                if 'PageResult<' not in seg:
                    continue
                path = (prefix + tail).replace('//', '/')
                if '{' in path:
                    continue
                out.append(path)
    return sorted(set(out))


def totals(path, tok):
    full = path + ('&' if '?' in path else '?') + 'pageNum=1&pageSize=1'
    st, d = call(full, tok)
    if st != 200:
        return st, None
    data = (d or {}).get('data') or {}
    return st, data.get('total')


def main():
    admin = login('admin', 'admin123')
    tenant = login('test_tenant', 'Test@1234')
    if not admin or not tenant:
        print('无法登录，检查账号')
        return 1

    paths = discover()
    print('=' * 74)
    print('运行时数据范围校验：%d 个列表接口' % len(paths))

    suspects, checked, skipped = [], 0, 0
    for p in paths:
        if any(p.startswith(x) or x in p for x in PUBLIC):
            skipped += 1
            continue
        st_a, t_a = totals(p, admin)
        st_t, t_t = totals(p, tenant)
        if st_a != 200 or t_a is None:
            continue
        checked += 1
        if st_t != 200:
            continue      # 租户无权限，跳过
        if t_t and t_a and int(t_t) == int(t_a):
            suspects.append('%s  管理员 %s / 租户 %s' % (p, t_a, t_t))

    print('  实际比对 %d 个（跳过公开接口 %d 个）' % (checked, skipped))
    if not suspects:
        print('  ✔ 未发现「租户与管理员条数相同」的接口')
        print('=' * 74)
        return 0
    print('  发现 %d 个疑似未限权接口：' % len(suspects))
    for s in suspects:
        print('    ✗ ' + s)
    print('=' * 74)
    return 1


if __name__ == '__main__':
    sys.exit(main())
