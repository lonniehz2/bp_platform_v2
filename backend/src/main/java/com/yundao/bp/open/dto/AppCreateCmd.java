package com.yundao.bp.open.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 创建开放平台应用。
 */
public record AppCreateCmd(

        @NotBlank(message = "应用名称不能为空")
        String appName,

        /** THIRD_PARTY / INTERNAL / GOV */
        String appType,

        String ownerOrg,
        String contactName,
        String contactPhone,

        /** IP 白名单（逗号分隔，空=不限） */
        String ipWhitelist,

        Integer qpsLimit,
        Integer dailyQuota,

        /** 授权接口范围（逗号分隔，* = 全部） */
        String scopeCodes,

        /** 有效期（yyyy-MM-dd，空=长期） */
        String expireDate
) {
}
