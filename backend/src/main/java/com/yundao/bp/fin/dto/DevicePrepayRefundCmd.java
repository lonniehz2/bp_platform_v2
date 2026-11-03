package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record DevicePrepayRefundCmd(
        Long meterPointId,
        BigDecimal amount,
        BigDecimal feeAmount,
        String reason
) {
}
