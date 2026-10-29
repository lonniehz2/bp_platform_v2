package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/** 历史账单按新规则重算：请求参数。 */
public record RecalcBillsCmd(
        Long orgId,
        Long feeItemId,
        LocalDate periodStart,
        LocalDate periodEnd,
        Boolean dryRun
) {
}
