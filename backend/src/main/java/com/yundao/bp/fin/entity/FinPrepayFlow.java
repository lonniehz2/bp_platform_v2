package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 预收余额流水。 */
@Data
@TableName("bp_fin_prepay_flow")
public class FinPrepayFlow {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long accountId;
    private Long contractId;
    /** IN / OUT / REFUND / ADJUST */
    private String flowType;
    private BigDecimal amount;
    private BigDecimal balanceAfter;
    private String bizType;
    private Long bizId;
    private String payChannel;
    private String tradeNo;
    private BigDecimal feeAmount;
    private BigDecimal actualAmount;
    private String remark;
    private LocalDateTime createTime;
}
