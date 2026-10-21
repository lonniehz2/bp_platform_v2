package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 创建补贴标准。
 *
 * <p>补贴值含义随 {@code subsidyMode} 变化：
 * <ul>
 *   <li>FIXED → 每月金额（元/月）</li>
 *   <li>BY_AREA → 单价（元/㎡·月）</li>
 *   <li>BY_PERSON → 人均（元/人·月）</li>
 *   <li>RATIO → 比例（0~1，如 0.6 表示补贴 60%）</li>
 * </ul>
 */
public record SubsidyStandardCreateCmd(

        @NotBlank(message = "标准编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String standardCode,

        @NotBlank(message = "标准名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String standardName,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        Long orgId,
        String incomeLevel,
        String familyType,
        String talentLevel,

        @NotBlank(message = "补贴方式不能为空")
        @Pattern(regexp = "FIXED|BY_AREA|BY_PERSON|RATIO", message = "补贴方式不合法")
        String subsidyMode,

        @NotNull(message = "补贴值不能为空")
        @DecimalMin(value = "0", message = "补贴值不能为负")
        BigDecimal subsidyValue,

        @DecimalMin(value = "0", message = "封顶金额不能为负")
        BigDecimal maxAmount,

        LocalDate effectiveStart,
        LocalDate effectiveEnd
) {
}
