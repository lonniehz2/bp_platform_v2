package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建告警（可由规则引擎、设备回调或人工上报触发）。
 */
public record AlertCreateCmd(

        @NotBlank(message = "告警类别不能为空")
        @Pattern(regexp = "SAFETY|DEVICE|BUSINESS|VIOLATION", message = "告警类别不合法")
        String alertCategory,

        @NotBlank(message = "告警类型不能为空")
        @Size(max = 40, message = "告警类型不能超过 40 字符")
        String alertType,

        @NotBlank(message = "告警级别不能为空")
        @Pattern(regexp = "URGENT|IMPORTANT|NORMAL", message = "告警级别不合法")
        String alertLevel,

        @NotBlank(message = "告警标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String alertTitle,

        @Size(max = 2000, message = "告警内容不能超过 2000 字符")
        String alertContent,

        String alertValue,
        String thresholdValue,

        Long ruleId,
        String ruleCode,
        Long orgId,
        Long spaceId,
        Long houseId,
        Long personId,
        String deviceId,
        Long contractId,
        String relatedIds
) {
}
