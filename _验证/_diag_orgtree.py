# -*- coding: utf-8 -*-
"""诊断组织树：DB 层级 + 前端递归 + 接口行为"""
import io
import json
import urllib.request

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute('SELECT COUNT(*) FROM bp_iam_org WHERE parent_id IS NULL')
print('根节点：%s' % cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM bp_iam_org WHERE parent_id IS NOT NULL')
print('非根节点：%s' % cur.fetchone()[0])
cur.execute('SELECT id, org_code, org_name, parent_id, org_level FROM bp_iam_org '
            'ORDER BY org_level, id LIMIT 12')
print('\n样例：')
for r in cur.fetchall():
    print('   %s | %s | %s | parent=%s | L%s' % r)
cur.execute('SELECT org_level, COUNT(*) FROM bp_iam_org GROUP BY org_level')
print('\n按层级：%s' % (cur.fetchall(),))
c.close()

BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    with urllib.request.urlopen(r, timeout=40) as x:
        return json.loads(x.read().decode()).get('data')


print('\n=== /orgs/children 无参 ===')
d = get('/api/v1/orgs/children')
print('返回 %d 条；其中 parentId 为空的 %d 条'
      % (len(d), sum(1 for x in d if not x.get('parentId'))))
print('前 3 条 parentId：%s' % [x.get('parentId') for x in d[:3]])

print('\n=== 前端 loadTree 逻辑 ===')
s = io.open(r'D:\Work\业务平台开发\frontend\src\views\Orgs.vue', encoding='utf-8').read()
i = s.find('async function loadTree')
j = s.find('onMounted', i)
print(s[i:j])
