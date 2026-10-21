package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 申请退款。
 */
public record RefundCreateCmd(

        Long paymentId,
        Long personId,
        Long contractId,

        @NotNull(message = "退款金额不能为空")
        @DecimalMin(value = "0.01", message = "退款金额必须大于 0")
        BigDecimal refundAmount,

        @NotBlank(message = "退款类型不能为空")
        @Pattern(regexp = "DEPOSIT|OVERPAY|OTHER", message = "退款类型不合法")
        String refundType,

        @Pattern(regexp = "^$|ORIGINAL|BANK|CASH", message = "退款渠道不合法")
        String refundChannel,

        String refundReason
) {
}
