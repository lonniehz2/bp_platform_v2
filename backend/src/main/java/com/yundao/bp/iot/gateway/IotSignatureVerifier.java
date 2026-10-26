package com.yundao.bp.iot.gateway;

import com.yundao.bp.iot.config.IotSettings;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * IoT 回调验签。
 *
 * <pre>
 * canonical = method + "\n" + path + "\n" + appId + "\n" + timestamp + "\n" + nonce
 *           + "\n" + sha256Hex(body)
 * signature = hex(HMAC-SHA256(appSecret, canonical))
 * </pre>
 */
@Component
public class IotSignatureVerifier {

    private static final Logger log = LoggerFactory.getLogger(IotSignatureVerifier.class);

    private final IotSettings settings;

    public IotSignatureVerifier(IotSettings settings) {
        this.settings = settings;
    }

    public boolean verify(String method, String path, String appId, String timestamp,
                          String nonce, String body, String signature) {
        if (appId == null || timestamp == null || nonce == null || signature == null) {
            return false;
        }
        String expectAppId = settings.getString("iot.callback.appId");
        if (expectAppId != null && !expectAppId.isBlank() && !expectAppId.equals(appId)) {
            log.warn("回调 appId 不匹配: {}", appId);
            return false;
        }
        long ts;
        try {
            ts = Long.parseLong(timestamp.trim());
        } catch (NumberFormatException e) {
            return false;
        }
        long tolerance = settings.timestampToleranceSeconds();
        if (Math.abs(System.currentTimeMillis() / 1000 - ts) > tolerance) {
            log.warn("回调时间戳超窗: {} 容忍 {}s", timestamp, tolerance);
            return false;
        }
        String secret = settings.getString("iot.callback.appSecret");
        if (secret == null || secret.isBlank()) {
            log.error("回调 appSecret 未配置，拒绝回调");
            return false;
        }
        String canonical = method.toUpperCase() + "\n" + path + "\n" + appId + "\n"
                + timestamp + "\n" + nonce + "\n" + sha256Hex(body);
        String calc = hmacHex(secret, canonical);
        return calc != null && calc.equalsIgnoreCase(signature.trim());
    }

    public static String sha256Hex(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(md.digest(
                    (text == null ? "" : text).getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return "";
        }
    }

    private static String hmacHex(String secret, String canonical) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return HexFormat.of().formatHex(mac.doFinal(
                    canonical.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return null;
        }
    }
}
