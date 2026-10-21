package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;

/**
 * 多项目批量出账（一次生成租金 + 物业费 + 能耗费等多张账单）。
 *
 * <p>典型用法：每月初对全租户一次性出「租金 + 物业费」。
 * 内部按收费项目逐个调用单项目出账，任一项目失败不影响其它项目。
 *
 * @param items        要出账的收费项目列表
 * @param periodStart  费用起始日
 * @param periodEnd    费用截止日
 * @param billPeriod   账期（YYY-MM）；为空则按 periodStart 自动生成
 * @param dueDate      缴费截止日；为空 = periodStart
 * @param orgId        限定组织
 * @param houseType    限定房源类型
 * @param contractIds  限定合同；为空 = 全部生效合同
 * @param quantityOverride 覆盖数量
 * @param dryRun       试运行
 */
public record GenerateBatchCmd(

        @NotEmpty(message = "收费项目列表不能为空")
        List<Item> items,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        String billPeriod,
        LocalDate dueDate,
        Long orgId,
        String houseType,
        List<Long> contractIds,
        Integer quantityOverride,
        Boolean dryRun
) {
    /** 每个收费项目可单独指定规则。 */
    public record Item(@NotNull(message = "收费项目ID不能为空") Long feeItemId, Long ruleId) {
    }
}
