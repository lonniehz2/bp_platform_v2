package com.yundao.bp.iam.dto;

import java.util.List;

/**
 * 当前用户信息。
 */
public record MeVO(
        Long userId,
        String username,
        String realName,
        String tenantId,
        Long orgId,
        String tenantName,
        String orgName,
        String userType,
        Boolean admin,
        List<String> permissions,
        List<Long> roleIds,
        String locale,
        Boolean mustChangePassword
) {
}
