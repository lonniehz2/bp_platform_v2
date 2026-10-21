# -*- coding: utf-8 -*-
"""修复②：为敏感路由声明 meta.perm，并补齐数据库权限（避免菜单被误隐藏）"""
import io
import pymysql
import re

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

# 只给「高风险」页面加 perm，且这些权限我会在库里补齐并授予 ADMIN
PERM = {
    'rbac': 'sys:rbac:view',
    'sys': 'sys:admin:view',
    'ops-center': 'sys:ops:view',
    'open': 'open:app:list',
    'gov': 'gov:report:list',
    'credits': 'credit:manage',
    'grants': 'grant:manage',
    'keyring': 'keyring:manage',
}

added = 0
for path, perm in PERM.items():
    pat = re.compile(r"(path:\s*'/%s',[\s\S]{0,400}?)(meta:\s*\{)([^}]*)(\})"
                     % re.escape(path))
    m = pat.search(s)
    if not m:
        print('  !! 未匹配 /%s' % path)
        continue
    if 'perm:' in m.group(3):
        continue
    new_meta = m.group(2) + m.group(3).rstrip().rstrip(',') + ", perm: '%s' " % perm + m.group(4)
    s = s[:m.start(2)] + new_meta + s[m.end(4):]
    added += 1

io.open(R, 'w', encoding='utf-8').write(s)
print('  ✓ 为 %d 条敏感路由加 meta.perm' % added)

# ---------- 数据库补齐权限并授予 ADMIN ----------
PERMS = [
    ('sys:rbac:view', '用户与权限-查看', 'API'),
    ('sys:admin:view', '系统支撑-查看', 'API'),
    ('sys:ops:view', '运维操作台-查看', 'API'),
    ('credit:manage', '信用惩戒-管理', 'API'),
    ('grant:manage', '通行授权-管理', 'API'),
    ('keyring:manage', '钥匙包-管理', 'API'),
]

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute("SELECT id FROM bp_iam_role WHERE role_code='ADMIN' AND tenant_id='350600'")
row = cur.fetchone()
role_id = row[0] if row else None
print('  ADMIN role_id=%s' % role_id)

import time
base = int(time.time()) * 1000 % 10 ** 15
for i, (code, name, typ) in enumerate(PERMS, 1):
    cur.execute("SELECT id FROM bp_iam_permission WHERE perm_code=%s", (code,))
    r = cur.fetchone()
    if r:
        pid = r[0]
    else:
        pid = 790000000000000500 + i
        cur.execute("""INSERT INTO bp_iam_permission
            (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
            VALUES (%s,NULL,%s,%s,%s,%s,'ENABLED',NOW())""",
                    (pid, code, name, typ, 500 + i))
    if role_id:
        cur.execute("""SELECT id FROM bp_iam_role_permission
                       WHERE role_id=%s AND permission_id=%s""", (role_id, pid))
        if not cur.fetchone():
            cur.execute("""INSERT INTO bp_iam_role_permission
                (id, tenant_id, role_id, permission_id, create_time)
                VALUES (%s,'350600',%s,%s,NOW())""",
                        (796000000000000500 + i, role_id, pid))
c.commit()

cur.execute("""SELECT p.perm_code FROM bp_iam_permission p
               JOIN bp_iam_role_permission rp ON rp.permission_id=p.id
               JOIN bp_iam_role r ON r.id=rp.role_id
               WHERE r.role_code='ADMIN'""")
have = {x[0] for x in cur.fetchall()}
c.close()

missing = [p[0] for p in PERMS if p[0] not in have]
print('  权限补齐结果：%d/%d 已授予 ADMIN%s'
      % (len(PERMS) - len(missing), len(PERMS),
         ('，缺：' + ','.join(missing)) if missing else ''))
