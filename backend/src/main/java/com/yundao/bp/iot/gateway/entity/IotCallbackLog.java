package com.yundao.bp.iot.gateway.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 回调报文日志（含验签结果与处理状态）。对应 {@code bp_dev_callback_log}。 */
@Data
@TableName("bp_dev_callback_log")
public class IotCallbackLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String appId;
    private String msgType;
    private String eventId;
    private Integer signOk;
    private String rawBody;
    private String sourceIp;
    private Integer isDuplicate;
    private String processStatus;
    private String errorMsg;
    private LocalDateTime receiveTime;
    private LocalDateTime createTime;
}
