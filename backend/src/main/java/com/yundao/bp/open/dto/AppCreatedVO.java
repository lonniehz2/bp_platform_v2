package com.yundao.bp.open.dto;

import com.yundao.bp.open.entity.OpenApp;

/**
 * 应用创建结果。
 *
 * <p>⚠️ {@code appSecret} <b>仅在此处明文返回一次</b>，之后无法再取回
 * （库里存的是不可逆摘要 + 原值加密位）。这是开放平台的基本安全约定。
 */
public record AppCreatedVO(
        Long id,
        String appKey,
        String appSecret,
        String appName,
        String appType,
        Integer qpsLimit,
        Integer dailyQuota,
        String scopeCodes,
        String expireDate,
        String appStatus
) {
    public static AppCreatedVO from(OpenApp a, String plainSecret) {
        return new AppCreatedVO(a.getId(), a.getAppKey(), plainSecret, a.getAppName(),
                a.getAppType(), a.getQpsLimit(), a.getDailyQuota(), a.getScopeCodes(),
                a.getExpireDate() == null ? null : a.getExpireDate().toString(),
                a.getAppStatus());
    }
}
