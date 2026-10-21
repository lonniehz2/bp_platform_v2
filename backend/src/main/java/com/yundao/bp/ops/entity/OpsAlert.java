package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 告警事件（统一告警中心）。对应 {@code bp_ops_alert}。
 */
@Data
@TableName("bp_ops_alert")
public class OpsAlert {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String alertNo;

    private Long ruleId;
    private String ruleCode;

    /** SAFETY / DEVICE / BUSINESS / VIOLATION */
    private String alertCategory;
    /** SUBLEASE / IDLE / CONTRACT_EXPIRE / DEVICE_OFFLINE / LOW_BATTERY / TAMPER / ... */
    private String alertType;
    /** URGENT / IMPORTANT / NORMAL */
    private String alertLevel;

    private String alertTitle;
    private String alertContent;
    /** 触发值（如占比 25%） */
    private String alertValue;
    /** 阈值快照 */
    private String thresholdValue;

    private Long orgId;
    private Long spaceId;
    private Long houseId;
    private Long personId;
    private String deviceId;
    private Long contractId;
    private String relatedIds;

    /** PENDING / HANDLING / HANDLED / IGNORED / ESCALATED */
    private String alertStatus;
    private Long handleUserId;
    private LocalDateTime handleTime;
    private String handleAction;
    private String handleResult;
    private Long workorderId;
    private LocalDateTime escalateTime;

    private LocalDateTime alertTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
