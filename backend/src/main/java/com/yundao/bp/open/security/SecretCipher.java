package com.yundao.bp.open.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * AppSecret 可逆加密存储。
 *
 * <p><b>为什么不能存哈希</b>：开放平台每次调用都要用 AppSecret 复算 HMAC 签名，
 * 因此密钥必须可还原。存哈希会导致签名永远校验不过。
 *
 * <p><b>为什么不能存明文</b>：数据库被读走等于所有第三方应用被接管。
 *
 * <p>方案：AES-256-GCM（带认证标签，防篡改），密文格式
 * {@code v1:Base64(iv||ciphertext||tag)}。主密钥来自配置项
 * {@code bp.open.secret-key}，<b>私有化部署时必须替换</b>。
 */
@Component
public class SecretCipher {

    private final SecretKeySpec key;
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final int IV_LEN = 12;
    private static final int TAG_BITS = 128;

    public SecretCipher(@Value("${bp.open.secret-key:BP-OPEN-DEFAULT-KEY-PLEASE-CHANGE}")
                        String masterKey) {
        try {
            // 任意长度主密钥 → 32 字节 AES key
            byte[] k = MessageDigest.getInstance("SHA-256")
                    .digest(masterKey.getBytes(StandardCharsets.UTF_8));
            this.key = new SecretKeySpec(k, "AES");
        } catch (Exception e) {
            throw new IllegalStateException("初始化密钥加密器失败", e);
        }
    }

    /** 加密。 */
    public String encrypt(String plain) {
        if (plain == null) {
            return null;
        }
        try {
            byte[] iv = new byte[IV_LEN];
            RANDOM.nextBytes(iv);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            byte[] enc = c.doFinal(plain.getBytes(StandardCharsets.UTF_8));
            byte[] all = new byte[iv.length + enc.length];
            System.arraycopy(iv, 0, all, 0, iv.length);
            System.arraycopy(enc, 0, all, iv.length, enc.length);
            return "v1:" + Base64.getEncoder().encodeToString(all);
        } catch (Exception e) {
            throw new IllegalStateException("加密失败", e);
        }
    }

    /** 解密。 */
    public String decrypt(String stored) {
        if (stored == null) {
            return null;
        }
        if (!stored.startsWith("v1:")) {
            // 兼容历史明文（不应出现，但避免直接崩）
            return stored;
        }
        try {
            byte[] all = Base64.getDecoder().decode(stored.substring(3));
            byte[] iv = new byte[IV_LEN];
            System.arraycopy(all, 0, iv, 0, IV_LEN);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            byte[] dec = c.doFinal(all, IV_LEN, all.length - IV_LEN);
            return new String(dec, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("解密失败（主密钥可能已更换）", e);
        }
    }
}
