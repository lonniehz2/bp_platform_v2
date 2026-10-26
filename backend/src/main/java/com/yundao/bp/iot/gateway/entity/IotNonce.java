package com.yundao.bp.iot.gateway.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 回调 Nonce（防重放）。对应 {@code bp_iot_nonce}。 */
@Data
@TableName("bp_iot_nonce")
public class IotNonce {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String appId;
    private String nonce;
    private LocalDateTime expireAt;
    private LocalDateTime createTime;
}
