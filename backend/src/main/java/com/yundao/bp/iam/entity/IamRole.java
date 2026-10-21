package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 角色。对应 `bp_iam_role`。
 */
@Data
@TableName("bp_iam_role")
public class IamRole {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String roleCode;
    private String roleName;
    /** SYSTEM / CUSTOM */
    private String roleType;
    /** ALL / TENANT / ORG / ORG_TREE / SELF */
    private String dataScope;
    private Integer sortNo;
    private String status;
    private String remark;
    private Integer isDeleted;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
