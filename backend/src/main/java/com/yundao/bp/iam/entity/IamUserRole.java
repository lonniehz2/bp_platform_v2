package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 用户-角色-组织关系。对应 `bp_iam_user_role`。
 */
@Data
@TableName("bp_iam_user_role")
public class IamUserRole {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long userId;
    private Long roleId;
    private Long orgId;
    private String createBy;
    private LocalDateTime createTime;
}
