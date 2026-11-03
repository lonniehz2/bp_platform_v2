package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 设备/表计预存流水。 */
@Data
@TableName("bp_fin_device_prepay_flow")
public class FinDevicePrepayFlow {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long accountId;
    private Long meterPointId;
    private Long contractId;
    private String flowType;
    private BigDecimal amount;
    private BigDecimal balanceAfter;
    private BigDecimal readingValue;
    private BigDecimal usageAmount;
    private String bizType;
    private Long bizId;
    private BigDecimal feeAmount;
    private BigDecimal actualAmount;
    private String remark;
    private LocalDateTime createTime;
}
