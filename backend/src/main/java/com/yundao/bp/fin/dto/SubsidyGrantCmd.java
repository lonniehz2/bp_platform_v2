package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 发放补贴（单户单期）。
 *
 * <p>金额由服务端按标准计算，不信任前端传入的金额。
 */
public record SubsidyGrantCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "受益人不能为空")
        Long personId,

        @NotBlank(message = "补贴期间不能为空")
        @Pattern(regexp = "^\\d{4}-\\d{2}$", message = "补贴期间格式应为 YYYY-MM")
        String subsidyPeriod,

        /** 可选：指定标准；不传则按保障类型/组织自动匹配 */
        Long standardId,

        @Pattern(regexp = "^$|FINANCE|BANK|OFFSET_RENT", message = "发放方式不合法")
        String payMode,

        String bankAccount
) {
}
