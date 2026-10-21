package com.yundao.bp.open.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.stereotype.Component;

/**
 * 开放平台签名与密钥工具。
 *
 * <p><b>签名算法</b>（与主流开放平台一致，第三方易实现）：
 *
 * <pre>
 * 待签串 = METHOD + "\n" + PATH + "\n" + timestamp + "\n" + nonce + "\n" + body
 * sign   = Hex(HMAC-SHA256(appSecret, 待签串))
 * </pre>
 *
 * <p><b>为什么带 timestamp + nonce</b>：只签 body 可被重放；加时间戳限制窗口，
 * 加 nonce 保证一次性。二者缺一都能被重放攻击。
 */
@Component
public class OpenSigner {

    private static final SecureRandom RANDOM = new SecureRandom();

    /** 允许的时间偏差（毫秒）：5 分钟 */
    public static final long MAX_SKEW_MS = 5 * 60 * 1000L;

    /** 生成 AppSecret（32 字节 hex，仅创建时明文返回一次）。 */
    public String newSecret() {
        byte[] b = new byte[32];
        RANDOM.nextBytes(b);
        return HexFormat.of().formatHex(b);
    }

    /** 生成 AppKey（带前缀便于识别）。 */
    public String newAppKey() {
        byte[] b = new byte[12];
        RANDOM.nextBytes(b);
        return "AK" + HexFormat.of().formatHex(b).toUpperCase();
    }

    /** 生成 nonce。 */
    public String newNonce() {
        byte[] b = new byte[8];
        RANDOM.nextBytes(b);
        return HexFormat.of().formatHex(b);
    }

    /** 拼接待签串。 */
    public String buildPayload(String method, String path, String timestamp, String nonce,
                               String body) {
        return (method == null ? "" : method.toUpperCase()) + "\n"
                + (path == null ? "" : path) + "\n"
                + (timestamp == null ? "" : timestamp) + "\n"
                + (nonce == null ? "" : nonce) + "\n"
                + (body == null ? "" : body);
    }

    /** 计算签名（HMAC-SHA256 十六进制小写）。 */
    public String sign(String appSecret, String payload) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(appSecret.getBytes(StandardCharsets.UTF_8),
                    "HmacSHA256"));
            return HexFormat.of().formatHex(
                    mac.doFinal(payload.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("签名计算失败", e);
        }
    }

    /** 恒定时间比较（防时序攻击）。 */
    public boolean verify(String expect, String actual) {
        if (expect == null || actual == null) {
            return false;
        }
        return MessageDigest.isEqual(expect.getBytes(StandardCharsets.UTF_8),
                actual.getBytes(StandardCharsets.UTF_8));
    }

    /** 时间戳是否在允许窗口内。 */
    public boolean freshTimestamp(long timestampMs, long nowMs) {
        return Math.abs(nowMs - timestampMs) <= MAX_SKEW_MS;
    }

    /** IP 是否在白名单内（逗号分隔；空表示不限）。 */
    public boolean ipAllowed(String whitelist, String clientIp) {
        if (whitelist == null || whitelist.isBlank()) {
            return true;
        }
        for (String w : whitelist.split(",")) {
            String t = w.trim();
            if (t.isEmpty()) {
                continue;
            }
            if ("*".equals(t) || t.equals(clientIp)) {
                return true;
            }
            // 支持简单前缀网段：192.168.1.*
            if (t.endsWith("*") && clientIp != null
                    && clientIp.startsWith(t.substring(0, t.length() - 1))) {
                return true;
            }
        }
        return false;
    }
}
