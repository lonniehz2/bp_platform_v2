package com.yundao.bp.iam.security;

import com.yundao.bp.common.exception.BizException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import org.springframework.stereotype.Component;

/**
 * 密码哈希（PBKDF2WithHmacSHA256）。
 *
 * <p><b>为什么不用 BCrypt</b>：BCrypt 需引入 `spring-security-crypto` 依赖；
 * 本项目坚持零新增依赖，改用 JDK 自带 PBKDF2（OWASP 推荐算法之一），
 * 迭代 12 万次 + 16 字节随机盐，强度足够。
 *
 * <p>存储格式：`pbkdf2$迭代次数$base64(盐)$base64(哈希)`，便于将来升级算法。
 */
@Component
public class PasswordHasher {

    private static final String ALGO = "PBKDF2WithHmacSHA256";
    private static final int ITERATIONS = 120_000;
    private static final int SALT_BYTES = 16;
    private static final int KEY_BITS = 256;
    private static final SecureRandom RANDOM = new SecureRandom();

    /** 生成哈希。 */
    public String hash(String raw) {
        if (raw == null || raw.isEmpty()) {
            throw BizException.paramInvalid("密码不能为空");
        }
        byte[] salt = new byte[SALT_BYTES];
        RANDOM.nextBytes(salt);
        byte[] dk = pbkdf2(raw, salt, ITERATIONS);
        return "pbkdf2$" + ITERATIONS + "$" + b64(salt) + "$" + b64(dk);
    }

    /** 校验密码（恒定时间比较，防时序攻击）。 */
    public boolean verify(String raw, String stored) {
        if (raw == null || stored == null) {
            return false;
        }
        String[] parts = stored.split("\\$");
        if (parts.length != 4 || !"pbkdf2".equals(parts[0])) {
            return false;
        }
        try {
            int iters = Integer.parseInt(parts[1]);
            byte[] salt = Base64.getDecoder().decode(parts[2]);
            byte[] expect = Base64.getDecoder().decode(parts[3]);
            byte[] actual = pbkdf2(raw, salt, iters);
            return MessageDigest.isEqual(expect, actual);
        } catch (Exception e) {
            return false;
        }
    }

    private static byte[] pbkdf2(String raw, byte[] salt, int iters) {
        try {
            PBEKeySpec spec = new PBEKeySpec(raw.toCharArray(), salt, iters, KEY_BITS);
            return SecretKeyFactory.getInstance(ALGO).generateSecret(spec).getEncoded();
        } catch (Exception e) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.SYSTEM_ERROR,
                    "密码哈希计算失败");
        }
    }

    private static String b64(byte[] b) {
        return Base64.getEncoder().encodeToString(b);
    }

    /** 随机令牌（32 字节）。 */
    public String newToken() {
        byte[] b = new byte[32];
        RANDOM.nextBytes(b);
        StringBuilder sb = new StringBuilder();
        for (byte x : b) {
            sb.append(String.format("%02x", x));
        }
        return sb.toString();
    }

    /** 手机号哈希（精确检索用）。 */
    public String phoneHash(String phone) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(("bp:" + phone).getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte x : d) {
                sb.append(String.format("%02x", x));
            }
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }
}
