package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 提交投诉/建议/咨询/表扬。
 */
public record ComplaintCreateCmd(

        @NotBlank(message = "类型不能为空")
        @Pattern(regexp = "COMPLAINT|SUGGEST|CONSULT|PRAISE", message = "类型不合法")
        String complaintType,

        @Pattern(regexp = "^$|MINIAPP|APP|PHONE|WALKIN|OTHER", message = "来源不合法")
        String source,

        @NotBlank(message = "标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String title,

        @Size(max = 2000, message = "内容不能超过 2000 字符")
        String content,

        String images,
        Long orgId,
        Long personId,
        String submitterName,
        String submitterPhone
) {
}
