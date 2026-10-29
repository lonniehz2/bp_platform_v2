package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PlatformAdminCreateCmd(
        @NotBlank(message = "管理员账号不能为空")
        @Size(max = 64) String username,

        @Size(max = 64) String realName,
        @Size(max = 32) String phone,
        @Size(max = 128) String email
) {
}
