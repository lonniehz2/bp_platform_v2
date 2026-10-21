package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 申请退租。
 */
public record TerminationCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "房源不能为空")
        Long houseId,

        @NotNull(message = "承租人不能为空")
        Long personId,

        @NotBlank(message = "退租类型不能为空")
        @Pattern(regexp = "NORMAL|EXPEL|EXPIRE|EXCHANGE|OTHER", message = "退租类型不合法")
        String terminationType,

        LocalDate planExitDate,
        String exitReason,

        /** 重庆：过渡期月数（腾退给 3 个月） */
        Integer transitionMonths,
        /** 过渡期租金倍率（期内 1.5） */
        java.math.BigDecimal transitionRentMultiplier,
        /** 成都：搬迁期月数（不超过 6） */
        Integer relocationMonths
) {
}
