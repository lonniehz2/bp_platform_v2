package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;

/**
 * 批量自动出账。
 *
 * <p>按「生效中的合同 × 收费项目」批量生成账单。数量取值规则：
 * <ul>
 *   <li>{@code BY_AREA}：用房源面积</li>
 *   <li>{@code BY_NIGHT}：用期间天数（短租/民宿）</li>
 *   <li>{@code BY_BED} / {@code BY_PERSON}：用房源 {@code maxCapacity}，可用 {@code quantityOverride} 覆盖</li>
 *   <li>{@code FIXED} / {@code BY_HOUSE}：1</li>
 *   <li>{@code METER}：<b>不支持批量</b>（需抄表读数），会被跳过并给出原因</li>
 * </ul>
 *
 * @param dryRun true=只试算不落库，用于验证计费规则是否正确
 */
public record GenerateBillsCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        /** 可选：指定计费规则；不传则用项目默认单价 */
        Long ruleId,

        /** 规则方式：AUTO 自动匹配（默认）/ MANUAL 指定 / NONE 不使用 */
        String ruleMode,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        /** 账期，如 2026-10；为空自动按 periodStart 生成 */
        String billPeriod,

        /** 缴费截止日；为空 = periodStart */
        LocalDate dueDate,

        /** 限定组织 */
        Long orgId,
        /** 限定房源类型（多业态） */
        String houseType,
        /** 限定合同 ID 列表（为空=全部生效合同） */
        List<Long> contractIds,

        /** 覆盖数量（BY_BED/BY_PERSON 时不按 maxCapacity） */
        Integer quantityOverride,

        /** 试运行，不落库 */
        Boolean dryRun
) {
}
