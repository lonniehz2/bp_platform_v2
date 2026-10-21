package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权操作审计。对应 `bp_grant_audit_log`。
 *
 * <p>⭐ ★ 级要求：授权操作必须<b>不可篡改可追溯</b>。
 * 因此本模块<b>不提供 update / delete 接口</b>，只追加。
 */
@Data
@TableName("bp_grant_audit_log")
public class GrantAuditLog {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    /** GRANT / REVOKE / FREEZE / UNFREEZE / TRANSFER */
    private String bizType;
    private Long bizId;

    private Long personId;
    private Long spaceId;

    private Long operatorId;
    private String operatorName;
    private String reason;

    private String beforeJson;
    private String afterJson;
    /** SUCCESS / FAILED */
    private String result;

    private LocalDateTime createTime;
}
