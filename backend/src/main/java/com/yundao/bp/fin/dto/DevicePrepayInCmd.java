package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record DevicePrepayInCmd(
        Long meterPointId,
        Long contractId,
        BigDecimal amount,
        String payChannel,
        String tradeNo,
        String remark
) {
}
