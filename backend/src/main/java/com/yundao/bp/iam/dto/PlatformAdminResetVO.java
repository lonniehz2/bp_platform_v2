package com.yundao.bp.iam.dto;

/** 重置/新建管理员结果：初始密码仅本次返回。 */
public record PlatformAdminResetVO(
        Long userId,
        String username,
        String initialPassword,
        Boolean mustChangePassword
) {
}
