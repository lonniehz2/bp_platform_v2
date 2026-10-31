package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record LateFeePolicyCmd(
        Long orgId,
        BigDecimal dailyRate,
        Integer graceDays,
        BigDecimal capRate
) {
}
