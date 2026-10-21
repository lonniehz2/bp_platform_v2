package com.yundao.bp.iot.legacy;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * AccessToken 管理：获取、缓存、提前续期。
 *
 * <p>平台约定 30 分钟过期。本实现<b>提前 5 分钟续期</b>，避免边界失效。
 * 线程安全：{@code synchronized} 保证并发下只取一次 token。
 */
public class YmdTokenManager {

    public static final String TOKEN_PATH = "/ymd/auth-service/sys/getAccessToken";

    private final YmdHttpTransport transport;
    private final YmdCredentials credentials;
    private final Duration ttl;
    private final Duration renewAhead;

    private volatile YmdToken current;

    public YmdTokenManager(YmdHttpTransport transport, YmdCredentials credentials) {
        this(transport, credentials, Duration.ofMinutes(30), Duration.ofMinutes(5));
    }

    public YmdTokenManager(YmdHttpTransport transport, YmdCredentials credentials,
                           Duration ttl, Duration renewAhead) {
        this.transport = transport;
        this.credentials = credentials;
        this.ttl = ttl;
        this.renewAhead = renewAhead;
    }

    /** 获取有效 token（必要时自动续期）。 */
    public synchronized YmdToken getToken() {
        YmdToken t = current;
        if (t != null && !t.isExpiringWithin(renewAhead.getSeconds())) {
            return t;
        }
        current = fetch();
        return current;
    }

    /** 强制刷新（如遇 99990008 token 失效时调用）。 */
    public synchronized YmdToken refresh() {
        current = fetch();
        return current;
    }

    private YmdToken fetch() {
        Instant now = Instant.now();
        // ⚠️ 实测：time 必须是【秒级】时间戳
        Map<String, String> params = new HashMap<>();
        params.put("appKey", credentials.appKey());
        params.put("appSecret", credentials.appSecret());
        params.put("time", String.valueOf(now.getEpochSecond()));
        params.put("version", credentials.version());
        params.put("sign", Md5Signer.sign(params));

        String resp = transport.postJson(TOKEN_PATH, params);
        String token = YmdJson.extractString(resp, "token");
        if (token == null || token.isBlank()) {
            throw new YmdApiException("取 token 失败（响应中无 token）: " + brief(resp), null, 200);
        }
        return new YmdToken(token, now, now.plus(ttl));
    }

    private static String brief(String s) {
        return s == null ? "" : (s.length() > 300 ? s.substring(0, 300) + "..." : s);
    }
}
