package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PlatformUpdateCmd(
        @NotBlank(message = "平台名称不能为空")
        @Size(max = 100) String tenantName,

        @Pattern(regexp = "GOV|ORG|ENTERPRISE", message = "平台类型不合法") String tenantType,

        @Size(max = 20) String regionCode,

        String contactName,
        String contactPhone
) {
}
