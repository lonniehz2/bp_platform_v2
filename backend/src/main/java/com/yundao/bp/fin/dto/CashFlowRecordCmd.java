package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 手工登记资金流水（正常业务流水由系统自动写入）。
 */
public record CashFlowRecordCmd(

        @NotNull(message = "流水类型不能为空")
        @Pattern(regexp = "INCOME|EXPENSE|TRANSFER|ADJUST", message = "流水类型不合法")
        String flowType,

        @Pattern(regexp = "^$|BILL|PAYMENT|REFUND|SUBSIDY|OTHER", message = "业务类型不合法")
        String bizType,

        Long bizId,

        @NotNull(message = "金额不能为空")
        BigDecimal amount,

        String remark
) {
}
