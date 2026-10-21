package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权下发明细（每设备一行）。对应 {@code bp_grant_task_detail}。
 */
@Data
@TableName("bp_grant_task_detail")
public class GrantTaskDetail {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long taskId;
    private String deviceId;
    private String deviceMac;
    private String lockId;
    private Long spaceId;
    private Long keyringId;

    /** PENDING / SUCCESS / FAILED / SKIPPED */
    private String detailStatus;
    private String errorCode;
    private String errorMsg;
    private Integer durationMs;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
