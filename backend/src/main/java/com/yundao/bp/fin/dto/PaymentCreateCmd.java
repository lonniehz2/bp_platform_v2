package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 登记收款。
 */
public record PaymentCreateCmd(

        @NotNull(message = "组织不能为空")
        Long orgId,
        Long personId,
        String payerName,

        @NotNull(message = "收款金额不能为空")
        @DecimalMin(value = "0.01", message = "收款金额必须大于 0")
        BigDecimal payAmount,

        @NotBlank(message = "收款渠道不能为空")
        @Pattern(regexp = "WECHAT|ALIPAY|BANK|BANK_TRANSFER|CASH|POS|SELF_TERMINAL|OTHER",
                message = "收款渠道不合法")
        String payChannel,

        String tradeNo,
        Long operatorId,
        /** 是否未知款项（来源不明，先挂账待查证） */
        Integer unknownFlag,
        String remark
) {
}
