# -*- coding: utf-8 -*-
"""补齐角色页面权限，并拆出资金流水专用权限。

问题
----
* 合同经办 / 房源管理 / 服务协同 三个角色**页面权限为 0** →
  登录后菜单空白，只能直接输 URL。
* 财务岗能看到「资金流水」菜单，但接口权限已收紧为 fin:bill:manage → 点进去 403。

处理
----
1. 新增 `fin:cashflow:view`，授予财务岗；接口改为要求该权限。
2. 按岗位职责补页面权限（page:<slug>:view）。
"""
import pymysql

DB = dict(host='192.168.31.153', port=33306, user='root',
          password='5677@Mysql', database='bp_platform', charset='utf8mb4')

# 岗位 → 应可见页面
ROLE_PAGES = {
    'CONTRACT_CLERK': ['contracts', 'contract-changes', 'terminations', 'exchanges',
                       'houses', 'persons', 'applications', 'todos', 'messages'],
    'ASSET_CLERK': ['houses', 'spaces', 'house-calendar', 'short-rent', 'devices',
                    'device-bind', 'dev-events', 'access', 'keyring', 'grants',
                    'workorders', 'todos', 'messages'],
    'SERVICE_CLERK': ['workorders', 'alerts', 'complaints', 'visits', 'appeals',
                      'credits', 'messages', 'todos', 'houses', 'persons'],
    'REVIEWER': ['applications', 'annual-reviews', 'persons', 'waitlist',
                 'publicities', 'todos', 'messages'],
    'ACCEPTOR': ['applications', 'waitlist', 'publicities', 'persons',
                 'allocations', 'todos', 'messages'],
}

conn = pymysql.connect(**DB)
cur = conn.cursor()


def perm_id(code, name=None, perm_type='MENU'):
    cur.execute('select id from bp_iam_permission where perm_code=%s', (code,))
    row = cur.fetchone()
    if row:
        return row[0]
    pid = abs(hash(code)) % 10 ** 14 + 8 * 10 ** 14
    cur.execute('''insert into bp_iam_permission
                   (id, perm_code, perm_name, perm_type, route_path, scenario,
                    sort_no, status, create_time)
                   values (%s,%s,%s,%s,%s,'PLATFORM',99,'ENABLED',now())''',
                (pid, code, name or code, perm_type, '/' + code.replace('page:', '').replace(':view', '')))
    print('  新建权限:', code)
    return pid


def role_id(code):
    cur.execute('select id from bp_iam_role where role_code=%s', (code,))
    row = cur.fetchone()
    return row[0] if row else None


def grant(rid, pid):
    cur.execute('select count(*) from bp_iam_role_permission '
                'where role_id=%s and permission_id=%s', (rid, pid))
    if cur.fetchone()[0]:
        return False
    cur.execute('''insert into bp_iam_role_permission
                   (id, tenant_id, role_id, permission_id, create_time)
                   values (%s,%s,%s,%s,now())''',
                (abs(hash((rid, pid))) % 10 ** 14, '350600', rid, pid))
    return True


# 1) 资金流水专用权限
print('资金流水权限：')
cf = perm_id('fin:cashflow:view', '查看资金流水')
for r in ['FINANCE', 'ADMIN', 'AUDITOR']:
    rid = role_id(r)
    if rid and grant(rid, cf):
        print('  授予', r)

# 2) 岗位页面权限
print('\n岗位页面权限：')
for role, pages in ROLE_PAGES.items():
    rid = role_id(role)
    if not rid:
        print('  缺角色:', role)
        continue
    n = 0
    for slug in pages:
        pid = perm_id('page:%s:view' % slug, '页面-%s' % slug)
        if grant(rid, pid):
            n += 1
    print('  %-16s 新增 %d 个页面权限' % (role, n))

conn.commit()

# 3) 复核
print('\n复核：')
cur.execute('''select r.role_code,
  sum(case when p.perm_code like 'page:%' then 1 else 0 end)
  from bp_iam_role r
  left join bp_iam_role_permission rp on rp.role_id=r.id
  left join bp_iam_permission p on p.id=rp.permission_id
  group by r.id order by 2 asc''')
for row in cur.fetchall():
    print('  %-18s 页面 %s' % (row[0], row[1]))
conn.close()
