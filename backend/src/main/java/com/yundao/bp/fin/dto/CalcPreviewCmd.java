package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 试算请求（不落库，用于验证计费规则是否正确）。
 */
public record CalcPreviewCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        /** 可选：指定规则；不传则用项目默认单价 */
        Long ruleId,

        BigDecimal area,
        Integer quantity,
        BigDecimal meterStart,
        BigDecimal meterEnd
) {
}
