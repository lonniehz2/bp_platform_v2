package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record DevicePrepayConsumeCmd(
        Long meterPointId,
        BigDecimal amount,
        BigDecimal readingValue,
        BigDecimal usageAmount,
        Long billId,
        String remark
) {
}
