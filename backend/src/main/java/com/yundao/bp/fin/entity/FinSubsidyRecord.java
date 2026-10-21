package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 补贴发放记录。对应 {@code bp_fin_subsidy_record}。
 */
@Data
@TableName("bp_fin_subsidy_record")
public class FinSubsidyRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String recordNo;

    private Long standardId;
    private Long contractId;
    private Long personId;
    private String personName;
    private Long orgId;

    /** 补贴期间，如 2026-10 */
    private String subsidyPeriod;

    /** 应发金额 */
    private BigDecimal subsidyAmount;
    /** 实发金额 */
    private BigDecimal paidAmount;

    /** FINANCE / BANK / OFFSET_RENT */
    private String payMode;
    private String bankAccount;

    /** PENDING / PAYING / SUCCESS / FAILED / RETURNED */
    private String recordStatus;
    private String financeBatchNo;
    private String failReason;
    private LocalDate issueDate;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
