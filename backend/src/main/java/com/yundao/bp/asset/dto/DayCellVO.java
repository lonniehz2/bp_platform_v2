package com.yundao.bp.asset.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 月历中的一天。
 */
public record DayCellVO(
        LocalDate date,
        String dayStatus,
        String dayStatusLabel,
        BigDecimal price,
        Long bookingId,
        String sourceType,
        String remark
) {
}
