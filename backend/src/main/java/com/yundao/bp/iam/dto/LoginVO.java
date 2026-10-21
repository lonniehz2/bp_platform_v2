package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

/**
 * 登录结果。
 */
public record LoginVO(
        String token,
        Long userId,
        String username,
        String realName,
        String tenantId,
        Long orgId,
        Boolean admin,
        LocalDateTime expireTime
) {
}
