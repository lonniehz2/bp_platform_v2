package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 录入抄表读数。
 *
 * @param reading 本次读数（必须 ≥ 上次读数）
 * @param billPeriod 生成账单时的账期（可空，默认读数的年月）
 */
public record MeterReadingCmd(
        @NotNull(message = "房源不能为空") Long houseId,
        @NotNull(message = "收费项目不能为空") Long feeItemId,
        @NotNull(message = "读数不能为空") BigDecimal reading,
        LocalDate readDate,
        String billPeriod,
        String remark) {
}
