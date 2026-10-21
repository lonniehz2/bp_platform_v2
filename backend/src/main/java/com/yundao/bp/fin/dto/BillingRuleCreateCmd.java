package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

/**
 * 创建计费规则。
 *
 * <p>{@code priceConfig} 按规则类型填：
 * <pre>
 *   STANDARD : {"price": 12.50}
 *   TIERED   : {"tiers":[{"limit":50,"price":3.0},{"limit":null,"price":5.0}]}
 *   DISCOUNT : {"rate": 0.9}
 *   EXEMPT   : {}
 * </pre>
 */
public record BillingRuleCreateCmd(

        @NotBlank(message = "规则编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String ruleCode,

        @NotBlank(message = "规则名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String ruleName,

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        Long orgId,
        /** 适用房源类型（多业态：PUBLIC_RENTAL / DORMITORY / HOTEL ...） */
        String houseType,
        String securityType,
        String incomeLevel,

        @NotBlank(message = "规则类型不能为空")
        @Pattern(regexp = "STANDARD|TIERED|DISCOUNT|EXEMPT", message = "规则类型不合法")
        String ruleType,

        @NotBlank(message = "价格配置不能为空")
        String priceConfig,

        LocalDate effectiveStart,
        LocalDate effectiveEnd,
        Integer priority
) {
}
