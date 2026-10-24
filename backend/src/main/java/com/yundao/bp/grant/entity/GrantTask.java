package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权下发任务。对应 {@code bp_grant_task}。
 *
 * <p>幂等键 {@code idempotent_key} 在库上有唯一索引，防止重复下发。
 */
@Data
@TableName("bp_grant_task")
public class GrantTask {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String taskNo;

    /** sha1(personId + spaceId + level + 有效期) —— 库上唯一 */
    private String idempotentKey;

    /** 下发关联号（回调 serviceId 对应） */
    private String serviceId;

    /** 回调到达时间 */
    private java.time.LocalDateTime callbackTime;

    /** 超时判定时间（默认下发后 3 分钟） */
    private java.time.LocalDateTime timeoutAt;

    /** GRANT / REVOKE / FREEZE / UNFREEZE */
    private String taskType;

    private Long personId;
    private Long entitlementId;
    /** 逗号分隔的钥匙包 ID */
    private String keyringIds;

    private Integer lockCount;
    private Integer successCount;
    private Integer failCount;

    private LocalDateTime validStart;
    private LocalDateTime validEnd;

    /** IoT 异步任务 ID（用于 syncTask/result/list 轮询） */
    private String iotTaskId;
    private String iotRequestNo;

    /** PENDING / DISPATCHING / SUCCESS / PARTIAL / FAILED */
    private String taskStatus;
    private Integer retryCount;
    private String lastError;

    /** CONTRACT / KEYRING_ADD / SPACE_CHANGE / MANUAL */
    private String triggerSource;

    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime dispatchTime;
    private LocalDateTime finishTime;
    private LocalDateTime updateTime;
}
