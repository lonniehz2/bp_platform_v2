package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 创建公示。
 *
 * <p>⭐ 合规：配租公示（ALLOCATION）公示期<b>不得少于 7 个自然日</b>。
 */
public record PublicityCreateCmd(

        @NotBlank(message = "公示类型不能为空")
        @Pattern(regexp = "QUALIFY|ALLOCATION|EXIT", message = "公示类型不合法")
        String publicityType,

        Long orgId,

        @NotBlank(message = "标题不能为空")
        String title,

        String content,

        @NotNull(message = "公示开始日期不能为空")
        LocalDate startDate,

        @NotNull(message = "公示结束日期不能为空")
        LocalDate endDate,

        String attachmentUrl
) {
}
