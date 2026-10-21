package com.yundao.bp.iot.sign;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.SortedMap;
import java.util.TreeMap;

/**
 * 规范请求串（Canonical Request）构造器。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §15.2.2。
 * <pre>
 * 规范串（7 行，以 \n 连接，末尾不加 \n）：
 *   METHOD \n
 *   PATH \n
 *   CANONICAL_QUERY \n
 *   CANONICAL_BODY_HASH \n
 *   TIMESTAMP \n
 *   NONCE \n
 *   KEY_VERSION
 * </pre>
 *
 * <p><b>为什么用规范串而不是拼 JSON</b>：规范串与字段顺序无关、可独立复现、
 * 且两侧可打印后逐字符比对 —— 这是排查签名失败的关键手段。
 */
public final class CanonicalRequest {

    private final String method;
    private final String path;
    private final SortedMap<String, String> query = new TreeMap<>();
    private String bodyHash;
    private String timestamp;
    private String nonce;
    private String keyVersion;

    public CanonicalRequest(String method, String path) {
        if (method == null || method.isBlank()) {
            throw new IllegalArgumentException("method 不能为空");
        }
        if (path == null || path.isBlank()) {
            throw new IllegalArgumentException("path 不能为空");
        }
        this.method = method.toUpperCase();
        this.path = normalizePath(path);
        this.bodyHash = sha256Hex(new byte[0]);
        // 若 path 里带了 ?query，自动解析进 query 集合（避免调用方忘记拆分）
        if (path.indexOf('?') >= 0) {
            queryFromUrl(path);
        }
    }

    /** 路径必须以 / 开头；去掉 query 部分（query 单独参与签名）。 */
    private static String normalizePath(String raw) {
        String p = raw;
        int q = p.indexOf('?');
        if (q >= 0) {
            p = p.substring(0, q);
        }
        if (!p.startsWith("/")) {
            p = "/" + p;
        }
        return p;
    }

    public CanonicalRequest query(String key, String value) {
        if (key != null && !key.isEmpty()) {
            query.put(key, value == null ? "" : value);
        }
        return this;
    }

    public CanonicalRequest queryAll(Map<String, String> params) {
        if (params != null) {
            params.forEach(this::query);
        }
        return this;
    }

    /** 从完整 URL 中解析 query（简单实现：按 & 与第一个 = 切分，值做 URL 解码）。 */
    public CanonicalRequest queryFromUrl(String url) {
        int q = url.indexOf('?');
        if (q < 0 || q == url.length() - 1) {
            return this;
        }
        String qs = url.substring(q + 1);
        for (String pair : qs.split("&")) {
            if (pair.isEmpty()) {
                continue;
            }
            int eq = pair.indexOf('=');
            if (eq < 0) {
                query(urlDecode(pair), "");
            } else {
                query(urlDecode(pair.substring(0, eq)), urlDecode(pair.substring(eq + 1)));
            }
        }
        return this;
    }

    public CanonicalRequest body(byte[] bodyBytes) {
        this.bodyHash = sha256Hex(bodyBytes == null ? new byte[0] : bodyBytes);
        return this;
    }

    public CanonicalRequest body(String bodyText) {
        return body(bodyText == null ? new byte[0] : bodyText.getBytes(StandardCharsets.UTF_8));
    }

    public CanonicalRequest timestamp(String ts) {
        this.timestamp = ts;
        return this;
    }

    public CanonicalRequest nonce(String n) {
        this.nonce = n;
        return this;
    }

    public CanonicalRequest keyVersion(String kv) {
        this.keyVersion = kv;
        return this;
    }

    /** 构造规范串。 */
    public String build() {
        StringBuilder sb = new StringBuilder(256);
        sb.append(method).append('\n');
        sb.append(path).append('\n');
        sb.append(canonicalQuery()).append('\n');
        sb.append(bodyHash).append('\n');
        sb.append(nvl(timestamp)).append('\n');
        sb.append(nvl(nonce)).append('\n');
        sb.append(nvl(keyVersion));
        return sb.toString();
    }

    /** 规范化 query：参数按 key 字典序升序，URL 编码后以 & 连接；无参数为空串。 */
    public String canonicalQuery() {
        if (query.isEmpty()) {
            return "";
        }
        List<String> parts = new ArrayList<>(query.size());
        for (Map.Entry<String, String> e : query.entrySet()) {
            parts.add(rfc3986Encode(e.getKey()) + "=" + rfc3986Encode(e.getValue()));
        }
        return String.join("&", parts);
    }

    // ==================== 工具方法 ====================

    private static String nvl(String s) {
        return s == null ? "" : s;
    }

    /**
     * RFC 3986 严格 URL 编码（与应用/x-www-form-urlencoded 不同）。
     *
     * <p><b>关键差异</b>：空格编码为 {@code %20} 而不是 {@code +}；
     * 只保留 {@code A-Za-z0-9-._~} 不编码。这是两侧签名不一致的头号原因。
     */
    public static String rfc3986Encode(String s) {
        if (s == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder(s.length() * 3);
        for (byte b : s.getBytes(StandardCharsets.UTF_8)) {
            int c = b & 0xFF;
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
                    || c == '-' || c == '.' || c == '_' || c == '~') {
                sb.append((char) c);
            } else {
                sb.append('%').append(HEX_UPPER[c >> 4]).append(HEX_UPPER[c & 0x0F]);
            }
        }
        return sb.toString();
    }

    private static final char[] HEX_UPPER = "0123456789ABCDEF".toCharArray();

    /** URL 解码（用于从 URL 还原 query 值）。 */
    public static String urlDecode(String s) {
        if (s == null || s.indexOf('%') < 0) {
            return s == null ? "" : s;
        }
        byte[] out = new byte[s.length()];
        int len = 0;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '%' && i + 2 < s.length()) {
                int hi = Character.digit(s.charAt(i + 1), 16);
                int lo = Character.digit(s.charAt(i + 2), 16);
                if (hi >= 0 && lo >= 0) {
                    out[len++] = (byte) ((hi << 4) + lo);
                    i += 2;
                    continue;
                }
            }
            out[len++] = (byte) ch;
        }
        return new String(out, 0, len, StandardCharsets.UTF_8);
    }

    /** SHA-256 十六进制小写。 */
    public static String sha256Hex(byte[] data) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return toHexLower(md.digest(data == null ? new byte[0] : data));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("JDK 不支持 SHA-256", e);
        }
    }

    public static String toHexLower(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(Character.forDigit((b >> 4) & 0x0F, 16));
            sb.append(Character.forDigit(b & 0x0F, 16));
        }
        return sb.toString();
    }

    /** 便于排障：把规范串转成可视化形式（\n 显示为 ⏎）。 */
    public static String visualize(String canonical) {
        return canonical == null ? "(null)" : canonical.replace("\n", " ⏎ ");
    }
}
