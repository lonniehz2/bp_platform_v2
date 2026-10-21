# -*- coding: utf-8 -*-
"""生成 RBAC 实体 + Mapper"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(name, table, fields, imports='', doc=''):
    body = '\n'.join(fields)
    return f'''package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{imports}
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{body}
}}
'''


def mapper(name):
    return f'''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.{name};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {name}Mapper extends BaseMapper<{name}> {{
}}
'''


DT = 'import java.time.LocalDateTime;'

F['iam/entity/IamUser.java'] = ent('IamUser', 'bp_iam_user', [
    '    private String tenantId;',
    '    private String username;',
    '    /** PBKDF2 哈希（算法$迭代$盐$值） */',
    '    private String passwordHash;',
    '    private LocalDateTime pwdUpdateTime;',
    '    private String realName;',
    '    private String phone;',
    '    private String phoneHash;',
    '    private String email;',
    '    private String avatar;',
    '    private Long personId;',
    '    private Long orgId;',
    '    /** STAFF / TENANT / GOV / PLATFORM */',
    '    private String userType;',
    '    private Integer isAdmin;',
    '    private Integer singleDevice;',
    '    private String deviceId;',
    '    private LocalDateTime lastLoginTime;',
    '    private String lastLoginIp;',
    '    private Integer loginCount;',
    '    /** ENABLED / DISABLED / LOCKED */',
    '    private String status;',
    '    private String remark;',
    '    private Integer isDeleted;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], DT, '系统用户。对应 `bp_iam_user`。')

F['iam/entity/IamRole.java'] = ent('IamRole', 'bp_iam_role', [
    '    private String tenantId;',
    '    private String roleCode;',
    '    private String roleName;',
    '    /** SYSTEM / CUSTOM */',
    '    private String roleType;',
    '    /** ALL / TENANT / ORG / ORG_TREE / SELF */',
    '    private String dataScope;',
    '    private Integer sortNo;',
    '    private String status;',
    '    private String remark;',
    '    private Integer isDeleted;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], DT, '角色。对应 `bp_iam_role`。')

F['iam/entity/IamPermission.java'] = ent('IamPermission', 'bp_iam_permission', [
    '    private Long parentId;',
    '    private String permCode;',
    '    private String permName;',
    '    /** MENU / BUTTON / API / FIELD */',
    '    private String permType;',
    '    private String routePath;',
    '    private String component;',
    '    private String icon;',
    '    private String scenario;',
    '    private Integer sortNo;',
    '    private String status;',
], 'import java.time.LocalDateTime;', '权限资源。对应 `bp_iam_permission`。')

F['iam/entity/IamUserRole.java'] = ent('IamUserRole', 'bp_iam_user_role', [
    '    private String tenantId;',
    '    private Long userId;',
    '    private Long roleId;',
    '    private Long orgId;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
], DT, '用户-角色-组织关系。对应 `bp_iam_user_role`。')

F['iam/entity/IamRolePermission.java'] = ent('IamRolePermission', 'bp_iam_role_permission', [
    '    private String tenantId;',
    '    private Long roleId;',
    '    private Long permissionId;',
    '    private LocalDateTime createTime;',
], DT, '角色-权限关系。对应 `bp_iam_role_permission`。')

F['iam/entity/IamSession.java'] = ent('IamSession', 'bp_iam_session', [
    '    private String tenantId;',
    '    private Long userId;',
    '    /** 令牌标识（随机串，DB 可撤销） */',
    '    private String tokenId;',
    '    /** WEB / APP / MINIAPP / SCREEN */',
    '    private String deviceType;',
    '    private String deviceId;',
    '    private String loginIp;',
    '    private LocalDateTime loginTime;',
    '    private LocalDateTime expireTime;',
    '    /** ACTIVE / LOGOUT / KICKED / EXPIRED */',
    '    private String status;',
], DT, '登录会话。对应 `bp_iam_session`。')

for n in ('IamUser', 'IamRole', 'IamPermission', 'IamUserRole',
          'IamRolePermission', 'IamSession'):
    F['iam/mapper/%sMapper.java' % n] = mapper(n)

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
