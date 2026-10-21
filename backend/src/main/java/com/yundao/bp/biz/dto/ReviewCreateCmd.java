package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 创建复核（年审/动态核查）。
 */
public record ReviewCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        Long contractId,
        Long houseId,

        @NotBlank(message = "复核年度不能为空")
        @Pattern(regexp = "^\\d{4}$", message = "复核年度格式应为 YYYY")
        String reviewYear,

        String reviewBatch,

        @NotBlank(message = "复核类型不能为空")
        @Pattern(regexp = "ANNUAL|DYNAMIC|SPECIAL", message = "复核类型不合法")
        String reviewType,

        String triggerReason
) {
}
