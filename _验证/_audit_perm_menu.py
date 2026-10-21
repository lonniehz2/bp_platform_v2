# -*- coding: utf-8 -*-
"""检查路由 meta.perm 与数据库权限码是否匹配（不匹配会导致菜单消失）"""
import io
import json
import re
import urllib.error
import urllib.request

import pymysql

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

# 解析每条路由的 path/title/perm
items = []
for m in re.finditer(r"\{\s*\n\s*path:\s*'/([a-z\-]+)',[\s\S]{0,400}?meta:\s*\{([^}]*)\}",
                     s):
    path, meta = m.group(1), m.group(2)
    tm = re.search(r"title:\s*'([^']+)'", meta)
    pm = re.search(r"perm:\s*'([^']+)'", meta)
    items.append({'path': path, 'title': tm.group(1) if tm else '',
                  'perm': pm.group(1) if pm else None})

print('路由 %d 条，其中声明 perm 的 %d 条'
      % (len(items), len([x for x in items if x['perm']])))

# 数据库中的权限码
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute("SELECT perm_code FROM bp_iam_permission")
db_perms = {r[0] for r in cur.fetchall()}
cur.execute("""SELECT p.perm_code FROM bp_iam_permission p
               JOIN bp_iam_role_permission rp ON rp.permission_id = p.id
               JOIN bp_iam_role r ON r.id = rp.role_id
               WHERE r.role_code='ADMIN' AND rp.is_deleted=0""")
admin_perms = {r[0] for r in cur.fetchall()}
c.close()

print('数据库权限 %d 个 ｜ 管理员拥有 %d 个' % (len(db_perms), len(admin_perms)))

print('\n① 路由声明了但数据库不存在 → 该菜单对所有人隐藏：')
bad = [x for x in items if x['perm'] and x['perm'] not in db_perms]
if bad:
    for x in bad:
        print('    /%-18s %-14s perm=%s' % (x['path'], x['title'], x['perm']))
else:
    print('    无')

print('\n② 路由声明了、库里有、但管理员未被授予 → 管理员看不到：')
bad2 = [x for x in items
        if x['perm'] and x['perm'] in db_perms and x['perm'] not in admin_perms]
if bad2:
    for x in bad2:
        print('    /%-18s %-14s perm=%s' % (x['path'], x['title'], x['perm']))
else:
    print('    无')

print('\n③ 未声明 perm 的路由（登录即可见）%d 条'
      % len([x for x in items if not x['perm']]))
