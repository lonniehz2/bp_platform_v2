package com.yundao.bp.iam.dto;

public record OperatorLoginVO(
        String token,
        Long operatorId,
        String username,
        String realName,
        Boolean mustChangePassword
) {
}
