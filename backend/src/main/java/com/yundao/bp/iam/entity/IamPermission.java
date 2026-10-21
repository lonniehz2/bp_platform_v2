package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 权限资源。对应 `bp_iam_permission`。
 */
@Data
@TableName("bp_iam_permission")
public class IamPermission {

    @TableId(type = IdType.INPUT)
    private Long id;
    private Long parentId;
    private String permCode;
    private String permName;
    /** MENU / BUTTON / API / FIELD */
    private String permType;
    private String routePath;
    private String component;
    private String icon;
    private String scenario;
    private Integer sortNo;
    private String status;
    private java.time.LocalDateTime createTime;
}
