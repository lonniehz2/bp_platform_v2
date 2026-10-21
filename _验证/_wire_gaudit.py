# -*- coding: utf-8 -*-
"""授权审计接入 GrantServiceImpl（授权/撤销）+ 补充权限数据"""
import io
import os

import pymysql

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'grant\service\impl\GrantServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'GrantAuditService' not in s:
    # 1) import + 可选注入
    s = s.replace('import com.yundao.bp.grant.service.GrantService;',
                  'import com.yundao.bp.grant.service.GrantAuditService;\n'
                  'import com.yundao.bp.grant.service.GrantService;', 1)
    s = s.replace('''    private final SnowflakeIdGenerator idGen;''',
                  '''    private final SnowflakeIdGenerator idGen;

    /** 授权审计（★ 级要求：授权操作必须可追溯） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private GrantAuditService grantAuditService;

    private void audit(String bizType, Long bizId, Long personId, Long spaceId,
                       String reason, String before, String after, String result) {
        if (grantAuditService == null) {
            return;
        }
        var u = com.yundao.bp.iam.security.LoginUser.get();
        grantAuditService.record(bizType, bizId, personId, spaceId,
                u == null ? null : u.userId(),
                u == null ? null : (u.realName() == null ? u.username() : u.realName()),
                reason, before, after, result);
    }
''', 1)

    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ GrantServiceImpl 注入审计组件')

# 2) 在 apply 返回前写审计
s = io.open(p, encoding='utf-8').read()
if 'audit("GRANT"' not in s:
    # apply 的 return 前插入
    import re
    # 找到 apply 方法体里的第一个 "return GrantVO.from(" 之后插入审计（在该 return 之前）
    m = re.search(r'(public GrantVO apply\(GrantApplyCmd cmd\) \{)', s)
    assert m, 'apply 锚点缺失'
    # 定位 apply 方法内的第一个 return GrantVO.from(
    start = m.end()
    idx = s.find('return GrantVO.from(', start)
    assert idx > 0, 'apply return 锚点缺失'
    ins = ('audit("GRANT", null, cmd.personId(), cmd.spaceId(), "新增加权",\n'
           '                null, "entitlement apply", "SUCCESS");\n        ')
    s = s[:idx] + ins + s[idx:]
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ apply 写授权审计')

# 3) revoke 写审计
s = io.open(p, encoding='utf-8').read()
if 'audit("REVOKE"' not in s:
    m = __import__('re').search(r'(public GrantVO revoke\(Long id, String reason\) \{)', s)
    assert m, 'revoke 锚点缺失'
    start = m.end()
    idx = s.find('return GrantVO.from(', start)
    assert idx > 0, 'revoke return 锚点缺失'
    ins = ('audit("REVOKE", id, null, null, reason, "entitlement revoke",\n'
           '                "revoked: " + id, "SUCCESS");\n        ')
    s = s[:idx] + ins + s[idx:]
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ revoke 写授权审计')

# 4) 补充权限数据
TENANT = '350600'
NOW = '2026-10-19 12:00:00'
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
cur.execute("DELETE FROM bp_iam_role_permission WHERE permission_id IN "
            "(SELECT id FROM bp_iam_permission WHERE perm_code IN "
            "('dev:access:report','grant:audit:list'))")
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code IN "
            "('dev:access:report','grant:audit:list')")
NEW = [('dev:access:report', '上报通行记录'), ('grant:audit:list', '授权审计查询')]
for i, (code, name) in enumerate(NEW, start=1):
    pid = 790000000000000000 + i
    cur.execute("""INSERT INTO bp_iam_permission
        (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
        VALUES (%s,NULL,%s,%s,'API',%s,'ENABLED',%s)""", (pid, code, name, 200 + i, NOW))
    cur.execute("""INSERT INTO bp_iam_role_permission
        (id, tenant_id, role_id, permission_id, create_time)
        VALUES (%s,%s,710000000000000001,%s,%s)""",
                (795000000000000000 + i, TENANT, pid, NOW))
c.commit()
cur.execute("SELECT COUNT(*) FROM bp_iam_permission WHERE perm_code IN "
            "('dev:access:report','grant:audit:list')")
print('  ✓ 新增权限 %d 条并授予管理员' % cur.fetchone()[0])
c.close()
