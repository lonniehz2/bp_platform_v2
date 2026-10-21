package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 资金流水。对应 {@code bp_fin_cash_flow}。
 *
 * <p>每一笔收付都留一条流水，金额<b>带符号</b>（收入为正、支出为负），
 * 便于直接求和计算净流入。
 */
@Data
@TableName("bp_fin_cash_flow")
public class FinCashFlow {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long accountSetId;
    private String flowNo;

    /** INCOME / EXPENSE / TRANSFER / ADJUST */
    private String flowType;
    /** BILL / PAYMENT / REFUND / SUBSIDY / OTHER */
    private String bizType;
    private Long bizId;

    /** 金额（正负） */
    private BigDecimal amount;
    private BigDecimal balanceAfter;
    private LocalDateTime flowTime;

    /** UNVERIFIED / VERIFIED / ABNORMAL */
    private String verifyStatus;
    private String verifyRemark;

    private LocalDateTime createTime;
}
