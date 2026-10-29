package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/** 账单计费明细（解释“为什么是这个金额”）。 */
public record BillExplainVO(
        Long billId,
        String billNo,
        String feeItemName,
        String calcMode,
        String calcModeLabel,
        BigDecimal unitPrice,
        BigDecimal area,
        Integer quantity,
        Integer days,
        BigDecimal months,
        String formula,
        BigDecimal amount,
        String remark,
        List<Line> lines
) {
    public record Line(String label, String value) {
    }
}
