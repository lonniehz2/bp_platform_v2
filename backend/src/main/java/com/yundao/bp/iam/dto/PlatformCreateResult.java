package com.yundao.bp.iam.dto;

/** 创建平台结果：初始密码仅本次返回。 */
public record PlatformCreateResult(
        PlatformVO platform,
        String adminUsername,
        String initialPassword
) {
}
