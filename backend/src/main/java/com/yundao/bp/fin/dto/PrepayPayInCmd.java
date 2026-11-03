package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

/** 预收充值。 */
public record PrepayPayInCmd(
        Long contractId,
        Long personId,
        BigDecimal amount,
        String payChannel,
        String tradeNo,
        String remark
) {
}
