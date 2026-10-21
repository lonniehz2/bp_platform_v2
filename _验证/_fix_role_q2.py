# -*- coding: utf-8 -*-
"""修复角色查询语句（bp_iam_role 确实有 tenant_id）"""
import io

P = r'D:\Work\业务平台开发\_验证\_seed_open_gov.py'
lines = io.open(P, encoding='utf-8').read().split('\n')

fixed = 0
out = []
for ln in lines:
    if 'FROM bp_iam_role' in ln and ('%s' in ln or '%' in ln):
        out.append('cur.execute("SELECT id, role_code, role_name FROM bp_iam_role '
                   'WHERE tenant_id=%s AND is_deleted=0", (TENANT,))')
        fixed += 1
        continue
    if ln.strip().startswith('# 角色表列因环境而异'):
        continue
    out.append(ln)

io.open(P, 'w', encoding='utf-8').write('\n'.join(out))
print('修复 %d 处角色查询' % fixed)
