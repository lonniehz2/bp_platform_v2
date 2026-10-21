package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 提交审核结果。
 *
 * @param stage        审核阶段 ACCEPT / FORM / JOINT / FINAL
 * @param dept         审核部门（联审时填：REAL_ESTATE / CIVIL / SOCIAL_SECURITY）
 * @param result       PASS / REJECT / SUPPLEMENT
 * @param opinion      审核意见
 * @param checkItems   核验项明细（JSON 字符串）
 * @param supplementDemand 需补件时的要求
 * @param rejectReason 不通过原因
 */
public record ReviewCmd(

        @NotBlank(message = "审核阶段不能为空")
        @Pattern(regexp = "ACCEPT|FORM|JOINT|FINAL", message = "审核阶段不合法")
        String stage,

        String dept,

        @NotBlank(message = "审核结果不能为空")
        @Pattern(regexp = "PASS|REJECT|SUPPLEMENT", message = "审核结果不合法")
        String result,

        String opinion,
        String checkItems,
        String supplementDemand,
        String rejectReason
) {
}
