package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 系统用户。对应 `bp_iam_user`。
 */
@Data
@TableName("bp_iam_user")
public class IamUser {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String username;
    /** PBKDF2 哈希（算法$迭代$盐$值） */
    private String passwordHash;
    private LocalDateTime pwdUpdateTime;
    private String realName;
    private String phone;
    private String phoneHash;
    private String email;
    private String avatar;
    private Long personId;
    private Long orgId;
    /** STAFF / TENANT / GOV / PLATFORM */
    private String userType;
    private Integer isAdmin;
    private Integer singleDevice;
    private String deviceId;
    private LocalDateTime lastLoginTime;
    private String lastLoginIp;
    private Integer loginCount;
    /** ENABLED / DISABLED / LOCKED */
    private String status;
    private String remark;
    private Integer isDeleted;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
