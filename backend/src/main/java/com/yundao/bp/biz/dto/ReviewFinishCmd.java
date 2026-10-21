package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 完成复核。
 *
 * @param checkResult   核验明细 JSON（收入/房产/人口变化等）
 * @param adjustContent 调整内容（结果 ADJUST 时）
 */
public record ReviewFinishCmd(

        @NotBlank(message = "复核结果不能为空")
        @Pattern(regexp = "KEEP|ADJUST|EXIT|PENDING", message = "复核结果不合法")
        String reviewResult,

        String checkResult,
        String adjustContent,
        Long reviewUserId,

        /** 下次复核日期；为空则默认次年同日 */
        String nextReviewDate
) {
}
