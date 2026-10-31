package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record UtilityShareVO(
        Long contractId,
        String contractNo,
        String lesseeName,
        Integer occupyDays,
        BigDecimal personDays,
        BigDecimal shareRatio,
        BigDecimal shareAmount
) {
}
