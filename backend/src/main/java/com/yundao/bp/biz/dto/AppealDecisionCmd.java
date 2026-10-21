package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 复议决定。
 *
 * @param resultEffect RESTORE 恢复资格 / CANCEL 取消资格 / ADJUST 调整标准 / NONE 无影响
 */
public record AppealDecisionCmd(

        @NotBlank(message = "决定结论不能为空")
        @Pattern(regexp = "UPHELD|REJECTED", message = "决定结论只能是 UPHELD 或 REJECTED")
        String decision,

        @Size(max = 2000, message = "调查核实情况不能超过 2000 字")
        String handleResult,

        @Size(max = 2000, message = "复核意见不能超过 2000 字")
        String reviewOpinion,

        @NotBlank(message = "结果影响不能为空")
        @Pattern(regexp = "RESTORE|CANCEL|ADJUST|NONE", message = "结果影响不合法")
        String resultEffect,

        Long handleUserId
) {
}
