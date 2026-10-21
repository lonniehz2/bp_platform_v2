# -*- coding: utf-8 -*-
"""诊断登录失败：查用户记录 + 直接调用登录接口对比"""
import json
import urllib.error
import urllib.request

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_iam_user' "
            "ORDER BY ORDINAL_POSITION")
cols = [r[0] for r in cur.fetchall()]
print('bp_iam_user 列：%s' % ', '.join(cols))

sel = ['id', 'username']
for x in ('tenant_id', 'status', 'is_admin', 'is_deleted', 'login_fail_count'):
    if x in sel:
        continue
    if x in cols:
        sel.append(x)
cur.execute('SELECT %s FROM bp_iam_user' % ', '.join(sel))
print('\n用户记录：')
for r in cur.fetchall():
    print('  ' + ' | '.join(str(v)[:28] for v in r))

# 密码哈希前缀
if 'password_hash' in cols:
    cur.execute('SELECT username, LEFT(password_hash, 24) FROM bp_iam_user')
    print('\n密码哈希前缀：')
    for r in cur.fetchall():
        print('  %-12s %s' % r)
c.close()

BASE = 'http://192.168.31.11:8080'


def login(body, tag):
    d = json.dumps(body).encode()
    req = urllib.request.Request(BASE + '/api/v1/auth/login', data=d, method='POST',
                                headers={'Content-Type': 'application/json',
                                         'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(req, timeout=20) as x:
            j = json.loads(x.read().decode())
            print('  %-28s %s %s' % (tag, j.get('code'),
                                     (j.get('message') or '')[:40]))
    except urllib.error.HTTPError as e:
        print('  %-28s HTTP %s' % (tag, e.code))
    except Exception as e:
        print('  %-28s %s' % (tag, type(e).__name__))


print('\n登录接口对比：')
login({'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}, '带 tenantId')
login({'username': 'admin', 'password': 'admin123'}, '不带 tenantId')
