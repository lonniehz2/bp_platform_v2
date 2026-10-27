package com.yundao.bp.dev.iot.token;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.iot.legacy.JdkHttpTransport;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/**
 * 真实取 Token：POST {baseUrl}/ymd/restful/token。
 *
 * <p>签名 = HMAC-SHA256(appId + "\n" + timestamp + "\n" + nonce, appSecret)，小写 hex。
 * 平台缓存 token，到期前 5 分钟自动重取。
 */
@Component
@ConditionalOnProperty(name = "bp.iot.token-mode", havingValue = "real")
public class RealIotTokenClient implements IotTokenClient {

    private static final Logger log = LoggerFactory.getLogger(RealIotTokenClient.class);
    private static final String TOKEN_PATH = "/ymd/restful/token";
    private static final Duration RENEW_AHEAD = Duration.ofMinutes(5);

    private final JdkHttpTransport transport;
    private final String appId;
    private final String appSecret;
    private final ObjectMapper json = new ObjectMapper();

    private volatile String cachedToken;
    private volatile Instant expireAt = Instant.EPOCH;

    public RealIotTokenClient(
            @Value("${ymd.iot.base-url:}") String baseUrl,
            @Value("${ymd.iot.credential.app-id:}") String appId,
            @Value("${ymd.iot.credential.app-secret:}") String appSecret) {
        this.transport = new JdkHttpTransport(baseUrl,
                Duration.ofMillis(3000), Duration.ofMillis(10000), false);
        this.appId = appId;
        this.appSecret = appSecret;
    }

    @Override
    public synchronized TokenInfo token() {
        if (cachedToken != null && Instant.now().isBefore(expireAt.minus(RENEW_AHEAD))) {
            return new TokenInfo(cachedToken, Duration.between(Instant.now(), expireAt).toSeconds());
        }
        if (appId == null || appId.isBlank() || appSecret == null || appSecret.isBlank()) {
            throw new IllegalStateException(
                    "未配置 IoT appId/appSecret（ymd.iot.credential.*），无法取 Token");
        }
        long ts = Instant.now().getEpochSecond();
        String nonce = UUID.randomUUID().toString().replace("-", "");
        Map<String, String> payload = new LinkedHashMap<>();
        payload.put("appId", appId);
        payload.put("timestamp", String.valueOf(ts));
        payload.put("nonce", nonce);
        payload.put("sign", sign(appId + "\n" + ts + "\n" + nonce));
        try {
            String raw = transport.postJson(TOKEN_PATH, payload);
            JsonNode node = json.readTree(raw == null ? "{}" : raw);
            String code = node.path("code").asText("0");
            if (!("0".equals(code) || "SUCCESS".equalsIgnoreCase(code))) {
                throw new IllegalStateException("取 Token 失败: " + node.path("message").asText());
            }
            JsonNode data = node.path("data");
            String token = data.path("token").asText(null);
            long expiresIn = data.path("expiresIn").asLong(7200);
            if (token == null || token.isBlank()) {
                throw new IllegalStateException("取 Token 响应缺少 data.token");
            }
            cachedToken = token;
            expireAt = Instant.now().plusSeconds(expiresIn);
            log.info("已取到 IoT Token，有效期 {} 秒", expiresIn);
            return new TokenInfo(token, expiresIn);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("取 Token 异常: " + e.getMessage(), e);
        }
    }

    private String sign(String text) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(appSecret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] out = mac.doFinal(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(out.length * 2);
            for (byte b : out) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException("Token 签名失败", e);
        }
    }
}
