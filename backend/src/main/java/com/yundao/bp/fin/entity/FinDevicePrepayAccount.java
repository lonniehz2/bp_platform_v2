package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 设备/表计预存账户。 */
@Data
@TableName("bp_fin_device_prepay_account")
public class FinDevicePrepayAccount {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long meterPointId;
    private Long contractId;
    private Long spaceId;
    private String deviceId;
    private BigDecimal balanceAmount;
    private BigDecimal totalIn;
    private BigDecimal totalOut;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
