package com.yundao.platform.common.auth;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class TokenService {

    private final byte[] secret;
    private final long ttlSeconds;

    public TokenService(@Value("${bp.auth.secret:dev-only-change-me}") String secret,
                        @Value("${bp.auth.ttl-seconds:28800}") long ttlSeconds) {
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
        this.ttlSeconds = ttlSeconds;
    }

    public String create(long userId, String tenantId, String username, String displayName) {
        long exp = System.currentTimeMillis() / 1000 + ttlSeconds;
        String payload = userId + "|" + tenantId + "|" + username + "|" + displayName + "|" + exp;
        String encoded = Base64.getUrlEncoder().withoutPadding()
                .encodeToString(payload.getBytes(StandardCharsets.UTF_8));
        return encoded + "." + sign(encoded);
    }

    public UserContext.Principal verify(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        String[] parts = token.split("\\.");
        if (parts.length != 2) {
            return null;
        }
        if (!sign(parts[0]).equals(parts[1])) {
            return null;
        }
        try {
            String payload = new String(Base64.getUrlDecoder().decode(parts[0]), StandardCharsets.UTF_8);
            String[] fields = payload.split("\\|", 5);
            if (fields.length != 5) {
                return null;
            }
            long exp = Long.parseLong(fields[4]);
            if (exp < System.currentTimeMillis() / 1000) {
                return null;
            }
            return new UserContext.Principal(Long.parseLong(fields[0]), fields[1], fields[2], fields[3]);
        } catch (Exception e) {
            return null;
        }
    }

    private String sign(String value) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            return Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(mac.doFinal(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("token 签名失败", e);
        }
    }
}
