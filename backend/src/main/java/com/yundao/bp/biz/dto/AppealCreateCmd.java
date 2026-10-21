package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 提出申诉/异议。
 *
 * @param daysFromNow 申诉期限天数（政策时限，如收到告知起 10 个工作日）；为空则不设期限
 */
public record AppealCreateCmd(

        @NotBlank(message = "业务类型不能为空")
        @Pattern(regexp = "APPLICATION|REVIEW|ANNUAL_REVIEW|PUBLICITY|EXIT",
                message = "业务类型不合法")
        String bizType,

        @NotNull(message = "关联业务ID不能为空")
        Long bizId,

        @NotNull(message = "申请人不能为空")
        Long personId,

        Long orgId,

        @NotBlank(message = "申诉类型不能为空")
        @Pattern(regexp = "SUBMIT|OBJECTION", message = "申诉类型不合法")
        String appealType,

        @NotBlank(message = "申诉理由不能为空")
        @Size(max = 2000, message = "理由不能超过 2000 字")
        String appealReason,

        @Size(max = 2000, message = "证据材料不能超过 2000 字")
        String appealEvidence,

        /** 申诉期限天数（工作日近似按自然日计，由业务配置） */
        Integer daysFromNow
) {
}
