package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * 多项目批量出账汇总。
 *
 * @param batchNo    批次号（便于审计与追溯）
 * @param totalGenerated 全部项目合计生成张数
 * @param totalSkipped   合计跳过张数
 * @param totalAmount    合计金额
 * @param dryRun         是否试运行
 * @param results        各项目明细结果
 */
public record GenerateBatchVO(
        String batchNo,
        int totalGenerated,
        int totalSkipped,
        BigDecimal totalAmount,
        boolean dryRun,
        List<ItemResult> results
) {
    /**
     * @param feeItemId   收费项目
     * @param feeItemName 项目名称
     * @param status      OK / FAILED
     * @param error       失败原因
     * @param detail      该项目的出账明细
     */
    public record ItemResult(Long feeItemId, String feeItemName, String status, String error,
                             GenerateResultVO detail) {
    }
}
