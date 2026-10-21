package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 计费规则。对应 {@code bp_fin_billing_rule}。
 *
 * <p>{@code price_config} 为 JSON，按 {@link com.yundao.bp.fin.constant.RuleType} 解释：
 * <pre>
 *   STANDARD : {"price": 12.50}
 *   TIERED   : {"tiers":[{"limit":50,"price":3.0},{"limit":null,"price":5.0}]}
 *   DISCOUNT : {"rate": 0.9}            // 9 折
 *   EXEMPT   : {}                        // 全额减免
 * </pre>
 */
@Data
@TableName("bp_fin_billing_rule")
public class FinBillingRule {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String ruleCode;
    private String ruleName;
    private Long feeItemId;

    /** 适用组织（NULL 全租户） */
    private Long orgId;
    /** 适用房源类型（多业态适配点） */
    private String houseType;
    private String securityType;
    private String incomeLevel;

    /** STANDARD / TIERED / DISCOUNT / EXEMPT */
    private String ruleType;
    /** 价格配置 JSON */
    private String priceConfig;

    private LocalDate effectiveStart;
    private LocalDate effectiveEnd;
    private Integer priority;
    private Integer ruleVersion;

    /** PENDING / APPROVED / REJECTED（政府限价审批） */
    private String approveStatus;
    private Long approveById;
    private LocalDateTime approveTime;

    /** ENABLED / DISABLED */
    private String status;

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
