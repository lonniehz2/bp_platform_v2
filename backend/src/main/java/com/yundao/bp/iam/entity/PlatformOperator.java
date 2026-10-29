package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台运营超管（跨平台）。 */
@Data
@TableName("bp_iam_platform_operator")
public class PlatformOperator {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String username;
    private String passwordHash;
    private String realName;
    private String status;
    private Integer mustChangePassword;
    private Integer failCount;
    private LocalDateTime lockedUntil;
    private LocalDateTime lastLoginTime;
    private Integer isDeleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
