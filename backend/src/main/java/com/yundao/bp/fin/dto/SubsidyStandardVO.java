package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.SubsidyMode;
import com.yundao.bp.fin.entity.FinSubsidyStandard;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 补贴标准视图。
 */
public record SubsidyStandardVO(
        Long id,
        String standardCode,
        String standardName,
        String securityType,
        Long orgId,
        String incomeLevel,
        String familyType,
        String talentLevel,
        String subsidyMode,
        String subsidyModeLabel,
        BigDecimal subsidyValue,
        BigDecimal maxAmount,
        LocalDate effectiveStart,
        LocalDate effectiveEnd,
        String status
) {
    public static SubsidyStandardVO from(FinSubsidyStandard e) {
        if (e == null) {
            return null;
        }
        SubsidyMode m;
        try {
            m = SubsidyMode.valueOf(e.getSubsidyMode());
        } catch (IllegalArgumentException ex) {
            m = SubsidyMode.FIXED;
        }
        return new SubsidyStandardVO(e.getId(), e.getStandardCode(), e.getStandardName(),
                e.getSecurityType(), e.getOrgId(), e.getIncomeLevel(), e.getFamilyType(),
                e.getTalentLevel(), e.getSubsidyMode(), m.label(), e.getSubsidyValue(),
                e.getMaxAmount(), e.getEffectiveStart(), e.getEffectiveEnd(), e.getStatus());
    }
}
