package com.yundao.bp.iot.credential.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 凭据同步记录。对应 {@code bp_iot_credential_sync}。 */
@Data
@TableName("bp_iot_credential_sync")
public class IotCredentialSync {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long keyringId;
    private Long personId;
    private String keyType;
    /** ADD / UPDATE / FREEZE / UNFREEZE / REMOVE */
    private String action;
    /** PENDING / SUCCESS / FAILED / SKIPPED */
    private String status;
    private String requestId;
    private String errorMsg;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
