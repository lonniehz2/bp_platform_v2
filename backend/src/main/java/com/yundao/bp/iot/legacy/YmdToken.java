package com.yundao.bp.iot.legacy;

import java.time.Instant;

/**
 * AccessToken 及其派生信息。
 *
 * <p>平台约定 token 有效期 <b>30 分钟</b>。{@code pwd} 为 {@code token.substring(0,25)}，
 * 是所有参数加解密的密钥口令。
 */
public final class YmdToken {

    private final String token;
    private final String pwd;
    private final Instant obtainedAt;
    private final Instant expiresAt;

    public YmdToken(String token, Instant obtainedAt, Instant expiresAt) {
        if (token == null || token.isBlank()) {
            throw new IllegalArgumentException("token 不能为空");
        }
        if (token.length() < 25) {
            throw new IllegalArgumentException("token 长度不足 25，无法派生密钥");
        }
        this.token = token;
        this.pwd = token.substring(0, 25);
        this.obtainedAt = obtainedAt;
        this.expiresAt = expiresAt;
    }

    public String token() {
        return token;
    }

    /** 密钥口令 = token 前 25 位。 */
    public String pwd() {
        return pwd;
    }

    public Instant obtainedAt() {
        return obtainedAt;
    }

    public Instant expiresAt() {
        return expiresAt;
    }

    /** 是否在 {@code skewSeconds} 内即将过期（用于提前续期）。 */
    public boolean isExpiringWithin(long skewSeconds) {
        return Instant.now().plusSeconds(skewSeconds).isAfter(expiresAt);
    }

    @Override
    public String toString() {
        return "YmdToken{token='" + (token.length() > 8 ? token.substring(0, 8) + "..." : "***")
                + "', expiresAt=" + expiresAt + "}";
    }
}
