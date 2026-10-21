package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 审计日志。对应 `bp_sys_audit_log`。
 *
 * <p><b>只追加不可修改</b>：不提供 update/delete 接口，
 * 保证关键动作（授权/资金/审核/权限）可追溯且不可篡改。
 */
@Data
@TableName("bp_sys_audit_log")
public class SysAuditLog {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    /** GRANT / FINANCE / REVIEW / PERMISSION / DATA / OTHER */
    private String auditType;
    /** CRITICAL / IMPORTANT / NORMAL */
    private String auditLevel;

    private String bizType;
    private Long bizId;

    private Long operatorId;
    private String operatorName;

    private String targetType;
    private String targetId;
    private String action;

    private String beforeJson;
    private String afterJson;
    private String reason;
    private String clientIp;

    private LocalDateTime auditTime;
    private LocalDateTime createTime;
}
