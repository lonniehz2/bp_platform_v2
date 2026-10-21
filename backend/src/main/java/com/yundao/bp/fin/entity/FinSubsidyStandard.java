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
 * 补贴标准。对应 {@code bp_fin_subsidy_standard}。
 */
@Data
@TableName("bp_fin_subsidy_standard")
public class FinSubsidyStandard {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String standardCode;
    private String standardName;

    /** PUBLIC / AFFORDABLE / TALENT / LOW_RENT */
    private String securityType;

    private Long orgId;
    /** 适用收入档位 */
    private String incomeLevel;
    /** 适用家庭类型 */
    private String familyType;
    /** 适用人才层次 */
    private String talentLevel;

    /** FIXED / BY_AREA / BY_PERSON / RATIO */
    private String subsidyMode;
    /** 补贴值（金额/单价/比例） */
    private BigDecimal subsidyValue;
    /** 单户月度封顶 */
    private BigDecimal maxAmount;

    private LocalDate effectiveStart;
    private LocalDate effectiveEnd;

    /** ENABLED / DISABLED */
    private String status;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
