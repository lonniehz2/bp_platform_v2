package com.yundao.bp.dev.iot.token;

/**
 * IoT 取 Token 客户端（平台 → IoT）。
 *
 * <p>配置 {@code bp.iot.token-mode=mock|real}；real 需配置 {@code ymd.iot.base-url}、
 * {@code ymd.iot.credential.app-id}、{@code ymd.iot.credential.app-secret}。
 *
 * <p>契约见 21_IoT侧需求规格说明书 §1。
 */
public interface IotTokenClient {

    /** 取当前有效 Token（内部按过期时间缓存，提前 5 分钟续期）。 */
    TokenInfo token();

    record TokenInfo(String token, long expiresInSeconds) {
    }
}
