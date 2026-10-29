package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PlatformCreateCmd(
        @NotBlank(message = "平台名称不能为空")
        @Size(max = 100, message = "平台名称不能超过 100 字") String tenantName,

        @NotBlank(message = "行政区划不能为空")
        @Size(max = 20, message = "行政区划编码过长") String regionCode,

        @Pattern(regexp = "GOV|ORG|ENTERPRISE", message = "平台类型不合法") String tenantType,

        String contactName,
        String contactPhone,

        @NotBlank(message = "管理员账号不能为空")
        @Size(max = 64) String adminUsername,

        @Size(max = 64) String adminRealName
) {
}
