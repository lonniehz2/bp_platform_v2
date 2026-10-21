package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * Webhook 推送日志。对应 `bp_open_webhook_log`。
 */
@Data
@TableName("bp_open_webhook_log")
public class OpenWebhookLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long hookId;
    private String eventType;
    private String eventId;
    private String payload;
    /** PENDING / SUCCESS / FAILED */
    private String pushStatus;
    private Integer retryCount;
    private Integer httpStatus;
    private String responseBody;
    private LocalDateTime pushTime;
    private LocalDateTime createTime;
}
