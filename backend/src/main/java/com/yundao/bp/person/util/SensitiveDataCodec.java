package com.yundao.bp.person.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.regex.Pattern;

/**
 * 敏感数据编解码：<b>密文 + 哈希 + 脱敏</b> 三列策略。
 *
 * <p>设计依据：{@code 03_数据库设计说明.md} §2（敏感数据规范）。
 * 表中每个敏感字段有三列：
 * <ul>
 *   <li>{@code xxx}：密文（可解密还原）</li>
 *   <li>{@code xxx_hash}：哈希（用于<b>精确检索与唯一性校验</b>，不可逆）</li>
 *   <li>{@code xxx_mask}：脱敏（用于<b>列表展示</b>，无需解密）</li>
 * </ul>
 *
 * <p><b>为什么要哈希列</b>：密文无法索引查询（每次加密结果不同）。
 * 加哈希列后可用等值查询（如"按身份证号找人"），并做唯一性校验。
 *
 * <p><b>为什么用固定盐哈希而非随机盐</b>：需要等值检索 ⇒ 必须确定性。
 * 因此哈希必须加<b>固定盐</b>（密钥），避免被彩虹表反查。
 *
 * <p>⚠️ 生产环境应把 {@code salt} 放入密钥管理，不写在代码/配置里。
 */
public final class SensitiveDataCodec {

    /** 哈希固定盐（生产应外部化） */
    private static final String DEFAULT_SALT = "bp-sensitive-salt-2026";
    private static final char[] HEX = "0123456789abcdef".toCharArray();

    private static final Pattern ID_CARD_PATTERN =
            Pattern.compile("^(\\d{17}[\\dXx]|\\d{15})$");
    private static final Pattern PHONE_PATTERN = Pattern.compile("^1[3-9]\\d{9}$");

    private SensitiveDataCodec() {
    }

    // ==================== 哈希（确定性，用于检索/唯一性）====================

    public static String hash(String plain) {
        return hash(plain, DEFAULT_SALT);
    }

    public static String hash(String plain, String salt) {
        if (plain == null) {
            return null;
        }
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            md.update((salt == null ? "" : salt).getBytes(StandardCharsets.UTF_8));
            byte[] d = md.digest(plain.trim().getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(64);
            for (byte b : d) {
                sb.append(HEX[(b >> 4) & 0x0F]).append(HEX[b & 0x0F]);
            }
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException("哈希计算失败", e);
        }
    }

    // ==================== 脱敏（展示用）====================

    /**
     * 身份证脱敏：保留前 6 后 4，中间掩码。
     * <pre>330106199001011219 → 330106********1219</pre>
     */
    public static String maskIdCard(String idCard) {
        if (idCard == null || idCard.length() < 8) {
            return idCard;
        }
        int keepFront = 6;
        int keepBack = 4;
        String s = idCard.trim();
        if (s.length() <= keepFront + keepBack) {
            return repeat('*', s.length());
        }
        return s.substring(0, keepFront)
                + repeat('*', s.length() - keepFront - keepBack)
                + s.substring(s.length() - keepBack);
    }

    /**
     * 手机号脱敏：保留前 3 后 4。
     * <pre>13800138000 → 138****8000</pre>
     */
    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 8) {
            return phone;
        }
        String s = phone.trim();
        return s.substring(0, 3) + "****" + s.substring(s.length() - 4);
    }

    /** 姓名脱敏：保留姓，其余掩码（两字名保留首位，三字及以上保留首尾）。 */
    public static String maskName(String name) {
        if (name == null || name.isEmpty()) {
            return name;
        }
        if (name.length() == 1) {
            return name;
        }
        if (name.length() == 2) {
            return name.charAt(0) + "*";
        }
        return name.charAt(0) + repeat('*', name.length() - 2) + name.charAt(name.length() - 1);
    }

    // ==================== 校验 ====================

    public static boolean isValidIdCard(String idCard) {
        return idCard != null && ID_CARD_PATTERN.matcher(idCard.trim()).matches();
    }

    public static boolean isValidPhone(String phone) {
        return phone != null && PHONE_PATTERN.matcher(phone.trim()).matches();
    }

    /**
     * 身份证校验位验证（GB 11643-1999）。
     *
     * @return 18 位时校验最后一位；15 位或格式不符返回 false
     */
    public static boolean verifyIdCardChecksum(String idCard) {
        if (idCard == null || idCard.length() != 18) {
            return false;
        }
        String s = idCard.trim().toUpperCase();
        int[] weights = {7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2};
        char[] checkCodes = {'1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2'};
        int sum = 0;
        for (int i = 0; i < 17; i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
            sum += (c - '0') * weights[i];
        }
        return checkCodes[sum % 11] == s.charAt(17);
    }

    /** 从身份证号推算出生日期（18 位）。 */
    public static java.time.LocalDate birthdayFromIdCard(String idCard) {
        if (idCard == null || idCard.length() < 14) {
            return null;
        }
        try {
            String ymd = idCard.substring(6, 14);
            return java.time.LocalDate.parse(ymd,
                    java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            return null;
        }
    }

    /** 从身份证号推算性别（18 位，第 17 位奇男偶女）。 */
    public static String genderFromIdCard(String idCard) {
        if (idCard == null || idCard.length() < 17) {
            return "U";
        }
        char c = idCard.charAt(16);
        if (c < '0' || c > '9') {
            return "U";
        }
        return ((c - '0') % 2 == 1) ? "M" : "F";
    }

    private static String repeat(char ch, int n) {
        StringBuilder sb = new StringBuilder(Math.max(0, n));
        for (int i = 0; i < n; i++) {
            sb.append(ch);
        }
        return sb.toString();
    }
}
