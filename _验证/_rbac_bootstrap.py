# -*- coding: utf-8 -*-
"""RBAC 数据准备：
1. 预置三个默认角色 TENANT / STAFF / SYSTEM（不存在则创建）
2. 清理测试残留角色（roleCode 以 WROLE / WR2 开头，或名为「实测角色」）
3. 按菜单生成页面级权限（每条路由一条 page:<slug>），让权限树与菜单对齐

用法：python _rbac_bootstrap.py [--dry]
"""
import io
import json
import os
import re
import sys
import urllib.request
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ROUTER = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
API = 'http://192.168.31.11:8080/api/v1'
DRY = '--dry' in sys.argv

DEFAULT_ROLES = [
    ('TENANT', '租户', 'SELF'),
    ('STAFF', '工作人员', 'ORG'),
    ('SYSTEM', '系统账号', 'ALL'),
]


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


def routes():
    """从路由文件提取 (path, title)"""
    s = io.open(ROUTER, encoding='utf-8').read()
    out = []
    for m in re.finditer(r"path:\s*'([^']+)'[^}]*?title:\s*'([^']+)'", s, re.S):
        path, title = m.group(1), m.group(2)
        if path.startswith('/:') or ':' in path:
            continue
        if path in ('/', '/login'):
            continue
        out.append((path, title))
    seen, uniq = set(), []
    for p, t in out:
        if p in seen:
            continue
        seen.add(p)
        uniq.append((p, t))
    return uniq


def main():
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']

    roles = call('/rbac/roles', token=token)['data']
    by_code = {r['roleCode']: r for r in roles}

    # 1) 默认角色
    for code, name, scope in DEFAULT_ROLES:
        if code in by_code:
            print('默认角色已存在：%s(%s)' % (code, name))
            continue
        if DRY:
            print('[dry] 将创建角色 %s(%s)' % (code, name))
            continue
        r = call('/rbac/roles', 'POST',
                 {'roleCode': code, 'roleName': name, 'dataScope': scope}, token)
        print('创建角色 %s(%s) -> %s' % (code, name, r.get('code')))

    # 2) 清理测试残留角色
    junk = [r for r in roles
            if r['roleCode'].startswith('WROLE') or r['roleCode'].startswith('WR2')
            or r['roleName'] == '实测角色']
    print('待清理测试角色：%d 个' % len(junk))
    if junk:
        for r in junk[:3]:
            print('   ', r['roleCode'], r['roleName'])
        if not DRY:
            import pymysql
            c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                                password='5677@Mysql', database='bp_platform', charset='utf8mb4')
            cur = c.cursor()
            ids = [r['id'] for r in junk]
            ph = ','.join(['%s'] * len(ids))
            cur.execute('delete from bp_iam_role_permission where role_id in (%s)' % ph, ids)
            cur.execute('delete from bp_iam_user_role where role_id in (%s)' % ph, ids)
            n = cur.execute('delete from bp_iam_role where id in (%s)' % ph, ids)
            c.commit()
            c.close()
            print('已清理角色 %d 个' % n)

    # 3) 按菜单生成页面权限
    perms = call('/rbac/permissions', token=token)['data']
    have = {p['permCode'] for p in perms}
    rs = routes()
    print('路由 %d 条，现有权限 %d 条' % (len(rs), len(perms)))
    created = 0
    for path, title in rs:
        slug = path.strip('/').replace('/', '-')
        code = 'page:%s:view' % slug
        if code in have:
            continue
        if DRY:
            print('   [dry] 新增权限 %s（%s）' % (code, title))
            continue
        r = call('/rbac/permissions', 'POST',
                 {'permCode': code, 'permName': title, 'permType': 'MENU',
                  'routePath': path, 'sortNo': 0}, token)
        if r.get('code') == 'BP00000':
            created += 1
    print('新增页面权限 %d 条' % created)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
