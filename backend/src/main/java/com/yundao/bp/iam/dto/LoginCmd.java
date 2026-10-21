package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 登录请求。
 */
public record LoginCmd(

        /**
         * 租户ID。
         *
         * <p>登录时尚未建立租户上下文，必须先由请求指定，否则租户拦截器会拒绝
         * （写入会话/更新登录信息都需 tenant_id）。多租户下登录名仅在租户内唯一。
         */
        String tenantId,

        @NotBlank(message = "登录名不能为空")
        String username,

        @NotBlank(message = "密码不能为空")
        String password,

        /** WEB / APP / MINIAPP / SCREEN */
        String deviceType,

        String deviceId
) {
}
