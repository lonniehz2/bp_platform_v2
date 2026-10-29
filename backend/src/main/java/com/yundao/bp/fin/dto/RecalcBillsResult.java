package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/** 历史账单重算结果。 */
public record RecalcBillsResult(
        int scanned,
        int changed,
        int skipped,
        BigDecimal oldTotal,
        BigDecimal newTotal,
        boolean dryRun,
        List<Item> items
) {
    /**
     * @param status CHANGED / SKIPPED / SAME
     */
    public record Item(Long billId, String billNo, String contractNo,
                       BigDecimal oldAmount, BigDecimal newAmount,
                       Integer days, String explain, String status, String reason) {
    }
}
