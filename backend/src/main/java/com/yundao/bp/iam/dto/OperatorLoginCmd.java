package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;

public record OperatorLoginCmd(
        @NotBlank(message = "账号不能为空") String username,
        @NotBlank(message = "密码不能为空") String password
) {
}
