package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * Webhook 订阅。对应 `bp_open_webhook`。
 */
@Data
@TableName("bp_open_webhook")
public class OpenWebhook {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String hookName;
    private String callbackUrl;
    /** 订阅事件（逗号分隔） */
    private String eventTypes;
    /** 签名密钥（HMAC-SHA256） */
    private String secretKey;
    private Integer retryTimes;
    private Integer timeoutMs;
    private String hookStatus;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
