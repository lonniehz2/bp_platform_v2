package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 角色-权限关系。对应 `bp_iam_role_permission`。
 */
@Data
@TableName("bp_iam_role_permission")
public class IamRolePermission {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long roleId;
    private Long permissionId;
    private LocalDateTime createTime;
}
