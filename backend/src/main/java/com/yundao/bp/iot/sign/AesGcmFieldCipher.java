package com.yundao.bp.iot.sign;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * 敏感字段级加密（AES-256-GCM）。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §15.2.3。仅对含个人敏感信息的字段加密
 * （如身份证、手机号），设备指令类接口仅签名不加密 —— 避免全量加密的性能损耗。
 *
 * <p>输出格式（Base64）：{@code IV(12) || ciphertext || tag(16)}
 *
 * <p>相比原设计（AES 模式未知、密钥由 {@code token.substring(0,25)} 派生）的改进：
 * <ul>
 *   <li>AEAD 模式（GCM）而非 CBC —— 避免填充预言与 IV 误用</li>
 *   <li>每次随机 12 字节 IV</li>
 *   <li>AAD 绑定 {@code appId + ":" + fieldName}，防止密文被挪用到其它字段</li>
 *   <li>密钥独立配置与版本管理</li>
 * </ul>
 */
public final class AesGcmFieldCipher {

    private static final String TRANSFORM = "AES/GCM/NoPadding";
    private static final int IV_BYTES = 12;
    private static final int TAG_BITS = 128;
    private static final SecureRandom RANDOM = new SecureRandom();

    private final byte[] key;
    private final String appId;

    /**
     * @param keyBase64 32 字节（256 位）密钥的 Base64
     * @param appId     参与 AAD 的应用标识
     */
    public AesGcmFieldCipher(String keyBase64, String appId) {
        if (keyBase64 == null || keyBase64.isBlank()) {
            throw new IllegalArgumentException("加密密钥不能为空");
        }
        byte[] k = Base64.getDecoder().decode(keyBase64.trim());
        if (k.length != 32) {
            throw new IllegalArgumentException("AES-256 要求 32 字节密钥，实际 " + k.length + " 字节");
        }
        this.key = k;
        this.appId = appId == null ? "" : appId;
    }

    public AesGcmFieldCipher(byte[] key32, String appId) {
        if (key32 == null || key32.length != 32) {
            throw new IllegalArgumentException("AES-256 要求 32 字节密钥");
        }
        this.key = key32.clone();
        this.appId = appId == null ? "" : appId;
    }

    /** 随机生成 32 字节密钥并返回 Base64（用于初始化密钥）。 */
    public static String newKeyBase64() {
        byte[] k = new byte[32];
        RANDOM.nextBytes(k);
        return Base64.getEncoder().encodeToString(k);
    }

    /** 加密字段明文，返回 Base64(IV||ciphertext||tag)。 */
    public String encrypt(String plain, String fieldName) {
        if (plain == null) {
            return null;
        }
        try {
            byte[] iv = new byte[IV_BYTES];
            RANDOM.nextBytes(iv);
            Cipher cipher = Cipher.getInstance(TRANSFORM);
            cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"),
                    new GCMParameterSpec(TAG_BITS, iv));
            cipher.updateAAD(aad(fieldName));
            byte[] ct = cipher.doFinal(plain.getBytes(StandardCharsets.UTF_8));
            byte[] out = new byte[iv.length + ct.length];
            System.arraycopy(iv, 0, out, 0, iv.length);
            System.arraycopy(ct, 0, out, iv.length, ct.length);
            return Base64.getEncoder().encodeToString(out);
        } catch (Exception e) {
            throw new IllegalStateException("字段加密失败: " + fieldName, e);
        }
    }

    /** 解密 Base64(IV||ciphertext||tag)；AAD 不符或密文被篡改会抛异常。 */
    public String decrypt(String cipherBase64, String fieldName) {
        if (cipherBase64 == null) {
            return null;
        }
        try {
            byte[] all = Base64.getDecoder().decode(cipherBase64.trim());
            if (all.length <= IV_BYTES) {
                throw new IllegalArgumentException("密文长度不足");
            }
            byte[] iv = new byte[IV_BYTES];
            System.arraycopy(all, 0, iv, 0, IV_BYTES);
            byte[] ct = new byte[all.length - IV_BYTES];
            System.arraycopy(all, IV_BYTES, ct, 0, ct.length);

            Cipher cipher = Cipher.getInstance(TRANSFORM);
            cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"),
                    new GCMParameterSpec(TAG_BITS, iv));
            cipher.updateAAD(aad(fieldName));
            return new String(cipher.doFinal(ct), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("字段解密失败（密钥/AAD 不匹配或密文被篡改）: " + fieldName, e);
        }
    }

    private byte[] aad(String fieldName) {
        return (appId + ":" + (fieldName == null ? "" : fieldName)).getBytes(StandardCharsets.UTF_8);
    }
}
