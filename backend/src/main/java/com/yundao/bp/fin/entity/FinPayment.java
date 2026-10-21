package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 收款单。对应 {@code bp_fin_payment}。
 */
@Data
@TableName("bp_fin_payment")
public class FinPayment {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String paymentNo;
    private Long accountSetId;

    private Long orgId;
    private Long personId;
    private String payerName;

    private BigDecimal payAmount;
    /** WECHAT / ALIPAY / BANK / BANK_TRANSFER / CASH / POS / SELF_TERMINAL / OTHER */
    private String payChannel;
    private LocalDateTime payTime;
    private String tradeNo;

    /** PENDING / SUCCESS / FAILED / REFUNDED */
    private String payStatus;
    /** UNRECONCILED / RECONCILED / PARTIAL */
    private String reconcileStatus;
    private BigDecimal reconciledAmount;
    private Integer unknownFlag;

    private Long operatorId;
    private String remark;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
