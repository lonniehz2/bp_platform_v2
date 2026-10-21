package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 账单。对应 {@code bp_fin_bill}。
 */
@Data
@TableName("bp_fin_bill")
public class FinBill {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String billNo;
    private Long accountSetId;

    private Long orgId;
    private Long contractId;
    private Long houseId;
    private Long spaceId;

    private Long personId;
    private String payerName;
    private String payerPhone;

    private Long feeItemId;
    /** 账期，如 2026-10 */
    private String billPeriod;
    private LocalDate periodStart;
    private LocalDate periodEnd;

    private BigDecimal billAmount;
    private BigDecimal discountAmount;
    private BigDecimal lateFee;
    private BigDecimal paidAmount;
    private BigDecimal waivedAmount;
    /** 应付金额 = 应收 - 减免 + 滞纳金 - 已收 - 已免 */
    private BigDecimal payableAmount;

    private LocalDate dueDate;
    /** UNPAID / PARTIAL / PAID / OVERDUE / WAIVED / CANCELLED */
    private String billStatus;
    private Integer overdueDays;
    /** AUTO / MANUAL / IMPORT */
    private String generateType;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
