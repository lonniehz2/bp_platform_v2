package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record EnergyStatVO(
        String period,
        BigDecimal totalUsage,
        BigDecimal submeterUsage,
        BigDecimal diffUsage,
        BigDecimal diffRate,
        String alertLevel
) {
}
