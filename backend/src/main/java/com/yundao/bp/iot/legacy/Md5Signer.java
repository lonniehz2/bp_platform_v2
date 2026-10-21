package com.yundao.bp.iot.legacy;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;
import java.util.TreeMap;

/**
 * 云门道 IoT 现网协议：请求签名。
 *
 * <p>算法（与官方 {@code MD5.java} 一致）：
 * <pre>
 *   StringToSign = 所有参数按 key 字典序拼接 "k1=v1&amp;k2=v2&amp;..."
 *   sign = MD5( StringToSign.getBytes("UTF-8") ) 的十六进制大写
 * </pre>
 *
 * <p><b>已用官方文档示例验证</b>：
 * <pre>
 *   loginname=t4nU902RvhliiPlMMcrzWw==&amp;logpwd=oFbqQ8bx8KvkHCI/Q2Kaxw==&amp;time=1553595995&amp;version=1.0.0
 *   → 46812299FB1BC111AC69A27F99068BE2
 * </pre>
 */
public final class Md5Signer {

    private static final char[] HEX_UPPER = "0123456789ABCDEF".toCharArray();

    private Md5Signer() {
    }

    /**
     * 计算签名。{@code sign} 键本身会被排除。
     *
     * @param params 参与签名的参数（值必须是"最终发送的值"，即加密后的值）
     */
    public static String sign(Map<String, ?> params) {
        if (params == null || params.isEmpty()) {
            return "";
        }
        // TreeMap 保证按 key 字典序
        TreeMap<String, String> sorted = new TreeMap<>();
        params.forEach((k, v) -> {
            if (!"sign".equals(k)) {
                sorted.put(k, v == null ? "" : String.valueOf(v));
            }
        });
        StringBuilder sb = new StringBuilder(256);
        for (Map.Entry<String, String> e : sorted.entrySet()) {
            if (sb.length() > 0) {
                sb.append('&');
            }
            sb.append(e.getKey()).append('=').append(e.getValue());
        }
        return md5Upper(sb.toString());
    }

    /** MD5（UTF-8）→ 十六进制大写。 */
    public static String md5Upper(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(digest.length * 2);
            for (byte b : digest) {
                sb.append(HEX_UPPER[(b >> 4) & 0x0F]).append(HEX_UPPER[b & 0x0F]);
            }
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException("MD5 计算失败", e);
        }
    }
}
