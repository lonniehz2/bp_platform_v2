package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** 平台信息维护：编码只读，仅允许改名称/类型/区域/状态。 */
public record PlatformInfoUpdateCmd(

        @NotBlank(message = "平台名称不能为空")
        @Size(max = 100, message = "平台名称不能超过 100 字")
        String tenantName,

        @Pattern(regexp = "GOV|ORG|ENTERPRISE", message = "平台类型不合法")
        String tenantType,

        @Size(max = 20, message = "区域编码不能超过 20 位")
        String regionCode,

        @Pattern(regexp = "ENABLED|DISABLED", message = "状态不合法")
        String status
) {
}
