package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 设备指令。对应 {@code bp_dev_command}。
 *
 * <p>平台不直连设备：指令经 IoT 平台下发，结果由回调 {@code command/ack} 回填。
 */
@Data
@TableName("bp_dev_command")
public class DevCommand {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String commandNo;

    /** LOCK_OPEN / DEVICE_REBOOT / DEVICE_SYNC_TIME / LOCK_MODE / ACCESS_OPEN / METER_SWITCH */
    private String commandType;

    private String deviceId;
    private String lockId;
    private String meterNo;

    /** 平台生成，回调按此关联 */
    private String requestId;

    private String paramsJson;

    /** PENDING / SENT / SUCCESS / FAILED / TIMEOUT / CANCELED */
    private String status;

    private Integer retryCount;
    private Integer maxRetry;
    private LocalDateTime timeoutAt;

    /** 拉合闸：延迟执行时间（到点才下发） */
    private LocalDateTime executeAfter;
    /** 拉合闸：可撤销截止时间（= executeAfter） */
    private LocalDateTime cancelDeadline;
    private LocalDateTime dispatchTime;
    private LocalDateTime ackTime;
    private String resultCode;
    private String resultMsg;
    private Integer costMs;

    private Long operatorId;
    private String operatorName;
    private String reason;

    /** 拉合闸：账单欠费金额快照 */
    private java.math.BigDecimal arrearsAmount;
    /** 拉合闸：目标房源 */
    private Long houseId;
    /** CONSOLE / API / SCHEDULE */
    private String source;

    /** 拉合闸审批：PENDING / APPROVED / REJECTED（其他指令为空） */
    private String approveStatus;
    private Long approveBy;
    private LocalDateTime approveTime;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
