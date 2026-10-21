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
 * 退款单。对应 {@code bp_fin_refund}。
 */
@Data
@TableName("bp_fin_refund")
public class FinRefund {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String refundNo;

    private Long paymentId;
    private Long personId;
    private Long contractId;

    private BigDecimal refundAmount;
    private String refundReason;
    /** DEPOSIT / OVERPAY / OTHER */
    private String refundType;
    /** ORIGINAL / BANK / CASH */
    private String refundChannel;
    /** PENDING / APPROVED / SUCCESS / FAILED / REJECTED */
    private String refundStatus;

    private Long approveById;
    private LocalDateTime approveTime;
    private LocalDateTime refundTime;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
