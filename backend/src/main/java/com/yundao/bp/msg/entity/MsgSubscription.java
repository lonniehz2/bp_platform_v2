package com.yundao.bp.msg.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 消息订阅配置。对应 `bp_msg_subscription`。
 */
@Data
@TableName("bp_msg_subscription")
public class MsgSubscription {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String bizType;
    /** ROLE / USER / PERSON / EXTERNAL */
    private String subscriberType;
    private String subscriberId;
    /** 渠道（逗号分隔） */
    private String channels;
    private String filterExpr;
    /** ENABLED / DISABLED */
    private String subStatus;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
