package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

public record UtilityAllocationVO(
        Long id,
        Long meterPointId,
        String meterName,
        String period,
        BigDecimal startReading,
        BigDecimal endReading,
        BigDecimal totalUsage,
        BigDecimal totalAmount,
        BigDecimal operatorBearAmount,
        List<UtilityShareVO> shares
) {
}
