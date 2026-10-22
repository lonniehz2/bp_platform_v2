# -*- coding: utf-8 -*-
"""去掉「用户类型」概念：新建用户直接选角色。

- UserCmd: userType → roleIds
- 建用户时按所选角色写入 user_role；未选则兜底绑定 STAFF 默认角色
- userType 列保留但固定写 STAFF（历史兼容）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'iam', 'controller', 'RbacController.java')

s = io.open(P, encoding='utf-8').read()
changed = []

# 1) UserCmd
if 'List<Long> roleIds' not in s:
    s = s.replace(
        'public record UserCmd(String username, String password, String realName, Long orgId,\n'
        '                          String userType) {\n    }',
        'public record UserCmd(String username, String password, String realName, Long orgId,\n'
        '                          java.util.List<Long> roleIds) {\n    }', 1)
    changed.append('UserCmd')

# 2) userType 固定 STAFF
if 'cmd.userType()' in s:
    s = s.replace('u.setUserType(cmd.userType() == null ? "STAFF" : cmd.userType());',
                  'u.setUserType("STAFF");  // 历史字段，系统概念上不再使用用户类型', 1)
    changed.append('userType')

# 3) 绑定逻辑：按 roleIds
marker = '// 按用户类型自动绑定默认角色'
i = s.find(marker)
if i >= 0:
    # 找到该段结束位置（下一个 "u.setPasswordHash(null);"）
    j = s.find('u.setPasswordHash(null);', i)
    new_block = (
        '// 直接按所选角色绑定（系统不再有「用户类型」概念）；\n'
        '        // 未选角色时兜底绑定 STAFF 默认角色，保证新账号不是空权限\n'
        '        java.util.List<Long> roleIds = cmd.roleIds();\n'
        '        if (roleIds == null || roleIds.isEmpty()) {\n'
        '            IamRole def = roleMapper.selectOne(new LambdaQueryWrapper<IamRole>()\n'
        '                    .eq(IamRole::getRoleCode, "STAFF").last("limit 1"));\n'
        '            roleIds = def == null ? java.util.List.of() : java.util.List.of(def.getId());\n'
        '        }\n'
        '        for (Long rid : roleIds) {\n'
        '            IamUserRole link = new IamUserRole();\n'
        '            link.setId(idGen.nextId());\n'
        '            link.setTenantId(TenantContext.tenantId());\n'
        '            link.setUserId(id);\n'
        '            link.setRoleId(rid);\n'
        '            link.setCreateTime(LocalDateTime.now());\n'
        '            userRoleMapper.insert(link);\n'
        '        }\n        ')
    s = s[:i] + new_block + s[j:]
    changed.append('绑定逻辑')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('RbacController 已改：', '、'.join(changed))
