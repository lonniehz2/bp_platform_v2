# -*- coding: utf-8 -*-
"""初始化 RBAC 数据：管理员账号 + 角色 + 权限
密码用与应用一致的 PBKDF2(pbkdf2$120000$salt$hash) 生成。
"""
import hashlib
import os
import secrets

import pymysql

ITER = 120_000


def hash_pwd(raw):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', raw.encode(), salt, ITER, 32)
    import base64
    return 'pbkdf2$%d$%s$%s' % (ITER, base64.b64encode(salt).decode(),
                                base64.b64encode(dk).decode())


TENANT = '350600'
NOW = '2026-10-19 12:00:00'

PERMS = [
    # (code, name, type, parent_code)
    ('iam:user:list', '用户列表', 'API', None),
    ('iam:user:create', '创建用户', 'API', None),
    ('iam:user:assign', '分配用户角色', 'API', None),
    ('iam:role:list', '角色列表', 'API', None),
    ('iam:role:create', '创建角色', 'API', None),
    ('iam:role:assign', '分配角色权限', 'API', None),
    ('iam:perm:list', '权限列表', 'API', None),
    ('iam:perm:create', '创建权限', 'API', None),
    ('asset:house:edit', '房源编辑', 'API', None),
    ('biz:contract:sign', '合同签约', 'API', None),
    ('fin:bill:generate', '批量出账', 'API', None),
    ('biz:credit:record', '记入失信', 'API', None),
]
ROLES = [
    ('ADMIN', '系统管理员', 'ALL'),
    ('ACCEPTOR', '受理岗', 'ORG'),
    ('REVIEWER', '审核岗', 'ORG'),
    ('FINANCE', '财务岗', 'TENANT'),
    ('VIEWER', '只读查看', 'TENANT'),
]
# 角色 -> 权限（VIEWER 只读）
ROLE_PERMS = {
    'ADMIN': [p[0] for p in PERMS],
    'ACCEPTOR': ['iam:user:list', 'iam:role:list'],
    'REVIEWER': ['iam:user:list'],
    'FINANCE': ['fin:bill:generate', 'iam:user:list'],
    'VIEWER': ['iam:user:list'],
}

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()

def nid(base):
    return base

# 清理旧演示数据
cur.execute("DELETE FROM bp_iam_role_permission WHERE tenant_id=%s", (TENANT,))
cur.execute("DELETE FROM bp_iam_user_role WHERE tenant_id=%s", (TENANT,))
cur.execute("DELETE FROM bp_iam_session WHERE tenant_id=%s", (TENANT,))
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code LIKE 'iam:%%' OR perm_code IN ('asset:house:edit','biz:contract:sign','fin:bill:generate','biz:credit:record')")
cur.execute("DELETE FROM bp_iam_role WHERE tenant_id=%s", (TENANT,))
cur.execute("DELETE FROM bp_iam_user WHERE tenant_id=%s", (TENANT,))

# 权限
perm_ids = {}
for i, (code, name, ptype, parent) in enumerate(PERMS, start=1):
    pid = 700000000000000000 + i
    cur.execute("""INSERT INTO bp_iam_permission
        (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
        VALUES (%s,%s,%s,%s,%s,%s,'ENABLED',%s)""",
                (pid, None, code, name, ptype, i, NOW))
    perm_ids[code] = pid

# 角色
role_ids = {}
for i, (code, name, scope) in enumerate(ROLES, start=1):
    rid = 710000000000000000 + i
    cur.execute("""INSERT INTO bp_iam_role
        (id, tenant_id, role_code, role_name, role_type, data_scope, sort_no, status,
         is_deleted, create_time, update_time)
        VALUES (%s,%s,%s,%s,'SYSTEM',%s,%s,'ENABLED',0,%s,%s)""",
                (rid, TENANT, code, name, scope, i, NOW, NOW))
    role_ids[code] = rid

# 角色-权限
rp_i = 0
for rcode, codes in ROLE_PERMS.items():
    for pc in codes:
        rp_i += 1
        cur.execute("""INSERT INTO bp_iam_role_permission
            (id, tenant_id, role_id, permission_id, create_time)
            VALUES (%s,%s,%s,%s,%s)""",
                    (720000000000000000 + rp_i, TENANT, role_ids[rcode],
                     perm_ids[pc], NOW))

# 用户：admin（管理员）
USERS = [
    (730000000000000001, 'admin', 'admin123', '系统管理员', 1, 'PLATFORM'),
    (730000000000000002, 'acceptor', 'acc123', '受理员小王', 0, 'STAFF'),
    (730000000000000003, 'viewer', 'view123', '只读用户', 0, 'STAFF'),
]
for uid, uname, pwd, rname, admin, utype in USERS:
    cur.execute("""INSERT INTO bp_iam_user
        (id, tenant_id, username, password_hash, real_name, user_type, is_admin,
         single_device, login_count, status, is_deleted, create_time, update_time)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0,0,'ENABLED',0,%s,%s)""",
                (uid, TENANT, uname, hash_pwd(pwd), rname, utype, admin, NOW, NOW))

# 用户-角色
UR = [
    (USERS[0][0], 'ADMIN'), (USERS[1][0], 'ACCEPTOR'), (USERS[2][0], 'VIEWER'),
]
ui = 0
for uid, rcode in UR:
    ui += 1
    cur.execute("""INSERT INTO bp_iam_user_role
        (id, tenant_id, user_id, role_id, create_time) VALUES (%s,%s,%s,%s,%s)""",
                (740000000000000000 + ui, TENANT, uid, role_ids[rcode], NOW))

c.commit()

cur.execute("SELECT COUNT(*) FROM bp_iam_user")
users = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_iam_role")
roles = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_iam_permission")
perms = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_iam_role_permission")
rps = cur.fetchone()[0]
print('初始化完成：用户 %d，角色 %d，权限 %d，角色权限 %d' % (users, roles, perms, rps))
print()
print('演示账号：')
for uid, uname, pwd, rname, admin, utype in USERS:
    print('  %-10s / %-10s  %s%s' % (uname, pwd, rname, '（管理员）' if admin else ''))
c.close()
