package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权对账差异。对应 `bp_grant_reconcile_diff`。
 */
@Data
@TableName("bp_grant_reconcile_diff")
public class GrantReconcileDiff {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String deviceId;
    private String lockId;
    private Long personId;
    /** IoT 侧授权对象账号（手机号） */
    private String targetUserMobile;
    /** LOCAL_MISSING / IOT_EXTRA / PERIOD_MISMATCH / VALUE_MISMATCH */
    private String diffType;
    private String localValue;
    private String iotValue;
    /** REGRANT / REVOKE / MANUAL / IGNORED */
    private String handleAction;
    /** PENDING / HANDLED / IGNORED */
    private String handleStatus;
    private LocalDateTime handleTime;
    private String handleRemark;
    private LocalDateTime createTime;
}
