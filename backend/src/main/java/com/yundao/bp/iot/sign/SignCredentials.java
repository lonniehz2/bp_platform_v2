package com.yundao.bp.iot.sign;

/**
 * IoT 平台调用凭证。
 *
 * <p>设计要点（{@code 02_架构与技术方案.md} §15.1 原则 1）：
 * <b>密钥与令牌分离</b>，禁止从 token 派生；支持 keyVersion 轮换。
 *
 * <p>安全要求：本对象禁止在日志中输出 secret（{@link #toString()} 已脱敏）。
 */
public final class SignCredentials {

    private final String appId;
    private final String appSecret;
    private final String keyVersion;

    public SignCredentials(String appId, String appSecret, String keyVersion) {
        if (appId == null || appId.isBlank()) {
            throw new IllegalArgumentException("appId 不能为空");
        }
        if (appSecret == null || appSecret.isBlank()) {
            throw new IllegalArgumentException("appSecret 不能为空");
        }
        this.appId = appId;
        this.appSecret = appSecret;
        this.keyVersion = (keyVersion == null || keyVersion.isBlank()) ? "k1" : keyVersion;
    }

    public String appId() {
        return appId;
    }

    public String appSecret() {
        return appSecret;
    }

    public String keyVersion() {
        return keyVersion;
    }

    @Override
    public String toString() {
        return "SignCredentials{appId='" + appId + "', appSecret='***', keyVersion='" + keyVersion + "'}";
    }
}
