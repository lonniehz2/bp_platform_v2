package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformAdminVO(
        Long userId,
        String username,
        String realName,
        String phone,
        String status,
        Boolean mustChangePassword,
        LocalDateTime lastLoginTime,
        LocalDateTime lockedUntil
) {
}
