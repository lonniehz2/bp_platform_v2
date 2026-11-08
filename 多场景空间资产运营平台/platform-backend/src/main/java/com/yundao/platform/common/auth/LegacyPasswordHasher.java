package com.yundao.platform.common.auth;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * 兼容旧保障房系统的 PBKDF2 密码格式：
 * pbkdf2$迭代次数$base64(盐)$base64(哈希)
 */
public final class LegacyPasswordHasher {

    private static final String ALGO = "PBKDF2WithHmacSHA256";
    private static final int KEY_BITS = 256;

    private LegacyPasswordHasher() {
    }

    public static boolean verify(String raw, String stored) {
        if (raw == null || stored == null || !stored.startsWith("pbkdf2$")) {
            return false;
        }
        String[] parts = stored.split("\\$");
        if (parts.length != 4) {
            return false;
        }
        try {
            int iterations = Integer.parseInt(parts[1]);
            byte[] salt = Base64.getDecoder().decode(parts[2]);
            byte[] expected = Base64.getDecoder().decode(parts[3]);
            PBEKeySpec spec = new PBEKeySpec(raw.toCharArray(), salt, iterations, KEY_BITS);
            byte[] actual = SecretKeyFactory.getInstance(ALGO).generateSecret(spec).getEncoded();
            return MessageDigest.isEqual(expected, actual);
        } catch (Exception e) {
            return false;
        }
    }
}
