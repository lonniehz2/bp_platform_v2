package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 押金台账。对应 {@code bp_fin_deposit}。
 *
 * <p>一台合同一条台账，贯穿"收押金 → 抵扣 → 退还"全过程。
 * 政策上限：成都规定押金不超过 1000 元，超限时 {@code over_cap_flag=1}。
 */
@Data
@TableName("bp_fin_deposit")
public class FinDeposit {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long personId;

    /** 应收押金 */
    private BigDecimal depositAmount;
    /** 已收押金 */
    private BigDecimal paidAmount;
    /** 已抵扣金额（如损坏赔偿） */
    private BigDecimal deductAmount;
    /** 已退还金额 */
    private BigDecimal refundAmount;
    /** 押金余额 = 已收 - 已抵扣 - 已退还 */
    private BigDecimal balanceAmount;

    /** HELD / PARTIAL_REFUND / REFUNDED / DEDUCTED */
    private String depositStatus;

    /** 政策规定上限（成都 1000 元） */
    private BigDecimal capAmount;
    private Integer isExempt;
    private String exemptReason;
    private Integer overCapFlag;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
