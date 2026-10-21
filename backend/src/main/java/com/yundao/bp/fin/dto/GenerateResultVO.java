package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * 批量出账结果。
 *
 * @param totalContracts 扫描到的生效合同数
 * @param generated      实际生成（或试算）的账单数
 * @param skipped        跳过数
 * @param skipReasons    跳过原因汇总
 * @param totalAmount    合计金额
 * @param dryRun         是否试运行
 * @param items          明细
 */
public record GenerateResultVO(
        int totalContracts,
        int generated,
        int skipped,
        List<String> skipReasons,
        BigDecimal totalAmount,
        boolean dryRun,
        List<Item> items
) {
    /**
     * @param contractId 合同
     * @param billId     生成的账单 ID（试运行时为 null）
     * @param quantity   参与计算的数量
     * @param amount     金额
     * @param explain    计算过程
     * @param status     OK / SKIPPED
     * @param reason     跳过或失败原因
     */
    public record Item(Long contractId, String contractNo, Long billId, Integer quantity,
                       BigDecimal amount, String explain, String status, String reason) {
    }
}
