package com.yundao.bp.iot.legacy;

import java.nio.charset.StandardCharsets;
import java.security.spec.KeySpec;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * 云门道 IoT 现网协议：AES 参数加解密。
 *
 * <p><b>算法来源</b>：云门道官方 {@code 算法参考.zip} 中的 {@code AES.java}，
 * 并经真实服务端调用验证（详见 {@code _验证/IoT对接规范-定稿.md}）。
 *
 * <p><b>参数（与官方源码逐项对应）</b>：
 * <ul>
 *   <li>IV：固定 {@code 1269571869323221}（16 ASCII 字节）</li>
 *   <li>盐：固定 {@code 4BDD60B281D31F1B70EC3AAA81F282BC}</li>
 *   <li>密钥派生：{@code PBKDF2WithHmacSHA1}，迭代 <b>100</b> 次，密钥 16 字节（AES-128）</li>
 *   <li>加密：{@code AES/CBC/PKCS5Padding}</li>
 *   <li>输出：Base64</li>
 * </ul>
 *
 * <p><b>官方源码要点</b>：{@code AES.java} 中的 {@code AES_PWD} 常量实际未被使用；
 * 密钥由调用方传入的 {@code pwd}（= {@code token.substring(0,25)}）经 PBKDF2 派生。
 *
 * <p><b>线程安全</b>：无共享可变状态，可单例复用（每次新建 Cipher）。
 *
 * <p><b>与二期协议的关系</b>：本类实现的是<b>现网既有协议</b>（安全性一般：MD5 + 固定 IV），
 * 一期直接对接；二期如需加固，另用 {@link com.yundao.bp.iot.sign.HmacSha256Strategy} 的
 * {@code v2-hmac-sha256} 协议，但需 IoT 侧同步改造。
 */
public final class AesCbcStrategy {

    /** 固定 IV（来自官方 AES.java 的 VIPARA） */
    public static final String IV = "1269571869323221";

    /** 固定盐（来自官方 AES.java 的 SALT） */
    public static final String SALT = "4BDD60B281D31F1B70EC3AAA81F282BC";

    /** PBKDF2 迭代次数（来自官方 AES.java） */
    public static final int ITERATIONS = 100;

    /** 密钥长度（字节），AES-128 */
    public static final int KEY_SIZE = 16;

    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";
    private static final String KEY_ALGORITHM = "AES";
    private static final String PBKDF2_ALGORITHM = "PBKDF2WithHmacSHA1";

    private static final byte[] IV_BYTES = IV.getBytes(StandardCharsets.US_ASCII);
    private static final byte[] SALT_BYTES = SALT.getBytes(StandardCharsets.US_ASCII);

    private AesCbcStrategy() {
    }

    /**
     * 由 {@code token.substring(0,25)} 派生 AES 密钥。
     *
     * <p>注意：Java 的 {@code PBKDF2WithHmacSHA1} 要求口令为 ASCII
     * （内部按 char 低 8 位转字节），与 Python/其他语言的 UTF-8 编码对 ASCII 等价。
     */
    public static SecretKey deriveKey(String pwd) {
        if (pwd == null || pwd.isEmpty()) {
            throw new IllegalArgumentException("派生密钥的口令不能为空");
        }
        try {
            KeySpec spec = new PBEKeySpec(pwd.toCharArray(), SALT_BYTES, ITERATIONS, KEY_SIZE * 8);
            SecretKeyFactory factory = SecretKeyFactory.getInstance(PBKDF2_ALGORITHM);
            byte[] keyBytes = factory.generateSecret(spec).getEncoded();
            return new SecretKeySpec(keyBytes, KEY_ALGORITHM);
        } catch (Exception e) {
            throw new IllegalStateException("PBKDF2 密钥派生失败", e);
        }
    }

    /** 便捷：直接返回派生后的密钥字节（便于与官方实现对账）。 */
    public static byte[] deriveKeyBytes(String pwd) {
        return deriveKey(pwd).getEncoded();
    }

    /**
     * 加密参数值。
     *
     * @param pwd   密钥口令（= token 前 25 位）
     * @param plain 明文
     * @return Base64 密文
     */
    public static String encrypt(String pwd, String plain) {
        if (plain == null) {
            return null;
        }
        try {
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, deriveKey(pwd), new IvParameterSpec(IV_BYTES));
            byte[] ct = cipher.doFinal(plain.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(ct);
        } catch (Exception e) {
            throw new IllegalStateException("AES 加密失败", e);
        }
    }

    /**
     * 解密参数值。
     *
     * @param pwd       密钥口令
     * @param base64Val Base64 密文（容忍内部空白字符，服务端返回可能带换行）
     * @return 明文
     */
    public static String decrypt(String pwd, String base64Val) {
        if (base64Val == null) {
            return null;
        }
        try {
            String cleaned = base64Val.replaceAll("\\s+", "");
            byte[] ct = Base64.getDecoder().decode(cleaned);
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, deriveKey(pwd), new IvParameterSpec(IV_BYTES));
            return new String(cipher.doFinal(ct), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("AES 解密失败（密钥不匹配或密文被篡改）", e);
        }
    }
}
