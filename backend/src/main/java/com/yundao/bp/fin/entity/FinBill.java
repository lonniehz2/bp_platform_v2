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
    /** 实际费用确认日（金额最终确定日，不含付款含义） */
    private LocalDate settlementDate;

    private BigDecimal billAmount;
    /** 本次实际使用的计价单价快照 */
    private BigDecimal unitPriceSnapshot;
    /** CONTRACT_RENT / FEE_ITEM */
    private String priceSource;
    private BigDecimal discountAmount;
    private BigDecimal lateFee;
    private BigDecimal paidAmount;
    private BigDecimal waivedAmount;
    /** 合同应享补贴金额（不等于已抵扣额） */
    private BigDecimal subsidyAmount;
    /** 应付金额 = 应收 - 减免 + 滞纳金 - 已收 - 已免 */
    private BigDecimal payableAmount;

    private LocalDate dueDate;
    /** 账单生成日（业务日期；create_time 为系统时间） */
    private LocalDate billDate;
    /** UNPAID / PARTIAL / PAID / OVERDUE / WAIVED / CANCELLED */
    private String billStatus;
    private Integer overdueDays;
    /** AUTO / MANUAL / IMPORT */
    private String generateType;
    private String remark;

    /** 命中的计费规则（快照，避免规则后续变更影响历史解释） */
    private Long ruleId;
    private Integer ruleVersion;
    private String ruleSnapshot;
    /** 本单计费数量（人/床/间夜/套） */
    private Integer billingQuantity;
    /** 计费天数（含首尾） */
    private Integer billingDays;
    /** 折算月数，如 1.483870 */
    private BigDecimal prorationMonths;
    private String quantityUnit;
    private String quantitySource;
    private String tierDetail;
    private Integer lateFeeDays;
    private String lateFeeDetail;

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
