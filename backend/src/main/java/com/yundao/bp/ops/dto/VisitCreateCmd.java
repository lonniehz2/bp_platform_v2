package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

/**
 * 创建走访任务。
 */
public record VisitCreateCmd(

        @NotBlank(message = "走访类型不能为空")
        @Pattern(regexp = "ROUTINE|VERIFY|COMPLAINT|ALERT|VACANCY", message = "走访类型不合法")
        String visitType,

        Long orgId,
        @NotNull(message = "走访房源不能为空")
        Long houseId,
        Long spaceId,
        Long personId,

        LocalDate planDate,

        Long visitUserId,
        String visitUserName,

        @Size(max = 500, message = "触发原因不能超过 500 字符")
        String triggerReason,

        Long alertId
) {
}
