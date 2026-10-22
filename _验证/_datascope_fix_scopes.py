# -*- coding: utf-8 -*-
"""修正数据范围：
1) 角色 data_scope 规范化为 ALL/ORG_SUB/ORG/SELF（库内存在 TENANT 等别名）
2) DataScopeService 兼容别名：TENANT→SELF
"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) 规范角色范围 ----------
SCOPE = {
    'ADMIN': 'ALL',
    'SYSTEM': 'ALL',
    'VIEWER': 'ALL',        # 只读但要能看全量
    'AUDITOR': 'ALL',       # 稽核需要全量只读
    'STAFF': 'ORG_SUB',
    'FINANCE': 'ORG',
    'ACCEPTOR': 'ORG',
    'REVIEWER': 'ORG',
    'CONTRACT_CLERK': 'ORG',
    'ASSET_CLERK': 'ORG',
    'SERVICE_CLERK': 'ORG',
    'TENANT': 'SELF',
}
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
cur.execute('select id, role_code, data_scope from bp_iam_role')
for rid, code, cur_scope in cur.fetchall():
    want = SCOPE.get(code)
    if want and want != cur_scope:
        cur.execute('update bp_iam_role set data_scope=%s where id=%s', (want, rid))
        print('  %-15s %s -> %s' % (code, cur_scope, want))
conn.commit()
cur.execute('select role_code, data_scope from bp_iam_role order by role_code')
print('当前角色范围：', ', '.join('%s=%s' % r for r in cur.fetchall()))
conn.close()

# ---------- 2) 服务兼容别名 ----------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'iam', 'datascope', 'DataScopeService.java')
s = io.open(P, encoding='utf-8').read()
if 'normalize' not in s:
    s = s.replace('''            for (IamRole r : roleMapper.selectBatchIds(roleIds)) {
                String scope = r.getDataScope() == null ? "SELF" : r.getDataScope();''',
                  '''            for (IamRole r : roleMapper.selectBatchIds(roleIds)) {
                String scope = normalize(r.getDataScope());''')
    helper = '''
    /** 归一化历史别名：TENANT/OWN 视同 SELF；未知值按最严处理。 */
    private String normalize(String raw) {
        if (raw == null || raw.isBlank()) {
            return "SELF";
        }
        String v = raw.trim().toUpperCase();
        if ("TENANT".equals(v) || "OWN".equals(v) || "PERSON".equals(v)) {
            return "SELF";
        }
        if (RANK.containsKey(v)) {
            return v;
        }
        return "SELF";
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + helper + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('DataScopeService：已加别名归一化')
