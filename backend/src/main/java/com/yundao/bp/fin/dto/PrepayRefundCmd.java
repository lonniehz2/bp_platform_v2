package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

/** 预收退款：amount 为申请退款金额，feeAmount 为渠道手续费，实际退款 = amount - feeAmount。 */
public record PrepayRefundCmd(
        Long contractId,
        BigDecimal amount,
        BigDecimal feeAmount,
        String payChannel,
        String tradeNo,
        String reason
) {
}
