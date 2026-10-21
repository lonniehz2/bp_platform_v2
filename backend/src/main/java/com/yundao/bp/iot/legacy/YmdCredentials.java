package com.yundao.bp.iot.legacy;

/**
 * IoT 平台凭证。
 *
 * <p>安全要求：{@link #toString()} 已脱敏，禁止在日志中输出 appSecret。
 */
public final class YmdCredentials {

    private final String appKey;
    private final String appSecret;
    private final String version;

    public YmdCredentials(String appKey, String appSecret, String version) {
        if (appKey == null || appKey.isBlank()) {
            throw new IllegalArgumentException("appKey 不能为空");
        }
        if (appSecret == null || appSecret.isBlank()) {
            throw new IllegalArgumentException("appSecret 不能为空");
        }
        this.appKey = appKey;
        this.appSecret = appSecret;
        // ⚠️ 实测：必须传 "1.0.0"；传 "V1.0.0" 会被平台再加 V 前缀，报"VV1.0.0无此版本接口"
        this.version = (version == null || version.isBlank()) ? "1.0.0" : version;
    }

    public String appKey() {
        return appKey;
    }

    public String appSecret() {
        return appSecret;
    }

    public String version() {
        return version;
    }

    @Override
    public String toString() {
        return "YmdCredentials{appKey='" + appKey + "', appSecret='***', version='" + version + "'}";
    }
}
