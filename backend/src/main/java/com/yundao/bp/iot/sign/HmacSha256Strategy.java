package com.yundao.bp.iot.sign;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * 协议 v2：HMAC-SHA256 签名。
 *
 * <p>⚠️ <b>状态：二期协议，一期未启用</b>
 *
 * <p><b>为什么一期不用它</b>：现网 IoT 平台使用的是 AES/MD5 协议
 * （见 {@link com.yundao.bp.iot.legacy.AesCbcStrategy}），已验证可直连。
 * 本类的 {@code v2-hmac-sha256} 是<b>更安全的替代设计</b>，但需要
 * <b>云门道侧同步改造平台</b>才能生效。
 *
 * <p><b>当年设计动机</b>（原算法被认为有问题）：
 * <ul>
 *   <li>MD5 → HMAC-SHA256（抗碰撞）</li>
 *   <li>密钥不再由 token 派生</li>
 *   <li>timestamp + nonce 防重放</li>
 * </ul>
 * 注：现网 AES/MD5 的密钥实际由 {@code PBKDF2WithHmacSHA1(token[:25], 固定盐, 100)} 派生，
 * 比"直接用 token 前 25 字节"要稳健；但仍使用 MD5 与固定 IV，安全性一般。
 *
 * <p><b>启用条件</b>：IoT 平台方实现并支持 {@code v2-hmac-sha256} 后，
 * 通过配置切换协议，两套实现可共存。
 * 详细对比见 {@code _验证/IoT对接规范-定稿.md} §5.3。
 *
 * <p>原描述：协议 v2：HMAC-SHA256 签名（一期默认实现）。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §15.2。替代原 AES+MD5 方案的三个问题：
 * <ul>
 *   <li>密钥不再从 token 派生（独立配置 + 可轮换）</li>
 *   <li>MD5 换为 HMAC-SHA256（抗碰撞、可并行、硬件加速）</li>
 *   <li>增加 timestamp + nonce 防重放</li>
 * </ul>
 *
 * <p>签名算法：
 * <pre>
 *   signature = Hex( HMAC_SHA256( key = appSecret, data = canonicalString ) )
 * </pre>
 *
 * <p><b>线程安全</b>：无共享可变状态（Mac 每次新建），可单例复用。
 */
public final class HmacSha256Strategy implements SignatureStrategy {

    public static final String PROTO = "v2-hmac-sha256";

    public static final String HDR_APP_ID     = "X-Ymd-AppId";
    public static final String HDR_TIMESTAMP  = "X-Ymd-Timestamp";
    public static final String HDR_NONCE      = "X-Ymd-Nonce";
    public static final String HDR_KEY_VER    = "X-Ymd-KeyVersion";
    public static final String HDR_SIGNATURE  = "X-Ymd-Signature";
    public static final String HDR_PROTO      = "X-Ymd-Proto";

    private static final String HMAC_ALG = "HmacSHA256";
    private static final SecureRandom RANDOM = new SecureRandom();

    @Override
    public String protocolVersion() {
        return PROTO;
    }

    @Override
    public SignResult sign(CanonicalRequest canonical, SignCredentials cred) {
        String ts = String.valueOf(System.currentTimeMillis());
        String nonce = newNonce();

        canonical.timestamp(ts).nonce(nonce).keyVersion(cred.keyVersion());
        String canonicalString = canonical.build();
        String signature = hmacSha256Hex(cred.appSecret(), canonicalString);

        Map<String, String> headers = new LinkedHashMap<>();
        headers.put(HDR_APP_ID, cred.appId());
        headers.put(HDR_TIMESTAMP, ts);
        headers.put(HDR_NONCE, nonce);
        headers.put(HDR_KEY_VER, cred.keyVersion());
        headers.put(HDR_SIGNATURE, signature);
        headers.put(HDR_PROTO, PROTO);

        return new SignResult(headers, canonicalString, signature);
    }

    @Override
    public boolean verify(String canonicalString, String signature, SignCredentials cred) {
        if (canonicalString == null || signature == null) {
            return false;
        }
        String expected = hmacSha256Hex(cred.appSecret(), canonicalString);
        return constantTimeEquals(expected, signature.trim());
    }

    // ==================== 基础算法 ====================

    /** 32 位十六进制随机串（16 字节熵）。 */
    public static String newNonce() {
        byte[] buf = new byte[16];
        RANDOM.nextBytes(buf);
        return CanonicalRequest.toHexLower(buf);
    }

    public static String hmacSha256Hex(String secret, String data) {
        return CanonicalRequest.toHexLower(hmacSha256(secret, data));
    }

    public static byte[] hmacSha256(String secret, String data) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALG);
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), HMAC_ALG));
            return mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new IllegalStateException("HMAC-SHA256 计算失败", e);
        }
    }

    /** 常量时间比较，防时序攻击。 */
    public static boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null) {
            return false;
        }
        return MessageDigest.isEqual(
                a.getBytes(StandardCharsets.UTF_8),
                b.getBytes(StandardCharsets.UTF_8));
    }
}
