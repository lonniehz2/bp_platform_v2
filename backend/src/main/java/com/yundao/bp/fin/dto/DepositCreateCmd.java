package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 建立押金台账（签约时调用）。
 *
 * <p>若 {@code capAmount} 非空且应收押金超过它，则自动标记 {@code overCapFlag=1}
 * 并在返回中提示（成都政策：押金不超过 1000 元）。
 */
public record DepositCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "应收押金不能为空")
        @DecimalMin(value = "0", message = "押金不能为负")
        BigDecimal depositAmount,

        /** 已收押金（为空则视为 0，后续可补收） */
        @DecimalMin(value = "0", message = "已收押金不能为负")
        BigDecimal paidAmount,

        /** 政策上限（成都 1000），为空则不校验 */
        BigDecimal capAmount,

        /** 是否免收（廉租标准免收） */
        Integer isExempt,
        String exemptReason
) {
}
