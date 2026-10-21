package com.yundao.bp.iot.tool;

import com.yundao.bp.iot.sign.AesGcmFieldCipher;
import com.yundao.bp.iot.sign.CanonicalRequest;
import com.yundao.bp.iot.sign.HmacSha256Strategy;
import com.yundao.bp.iot.sign.SignCredentials;
import com.yundao.bp.iot.sign.SignatureStrategy;

import java.util.Map;

/**
 * YmdCryptoVerify —— IoT 协议签名/加密验证工具（里程碑 M0）。
 *
 * <p>用途：
 * <ol>
 *   <li><b>自测</b>：校验本实现是否符合设计（固定向量的 HMAC/SHA256/GCM 往返）</li>
 *   <li><b>联调</b>：生成签名头并打印规范串，供云门道 IoT 侧逐字符比对</li>
 *   <li><b>验签</b>：用给定规范串与签名做校验，快速定位差异</li>
 * </ol>
 *
 * <p>用法：
 * <pre>
 *   java com.yundao.bp.iot.tool.YmdCryptoVerify selftest
 *   java ...YmdCryptoVerify sign --appId A --secret S --method POST --path /v1/lock/open
 *                                 [--query "a=1&b=2"] [--body "{}"] [--keyVersion k1]
 *   java ...YmdCryptoVerify verify --secret S --canonical "..." --signature "..."
 *   java ...YmdCryptoVerify genkey
 *   java ...YmdCryptoVerify enc --key K --appId A --field idCard --value 110101199001011234
 *   java ...YmdCryptoVerify dec --key K --appId A --field idCard --value BASE64
 * </pre>
 */
public final class YmdCryptoVerify {

    private static final HmacSha256Strategy HMAC = new HmacSha256Strategy();

    public static void main(String[] args) {
        if (args.length == 0) {
            usage();
            System.exit(2);
        }
        String cmd = args[0];
        Map<String, String> opt = parseOptions(args, 1);
        try {
            switch (cmd) {
                case "selftest" -> {
                    boolean ok = selftest();
                    System.exit(ok ? 0 : 1);
                }
                case "sign" -> doSign(opt);
                case "verify" -> doVerify(opt);
                case "genkey" -> System.out.println(AesGcmFieldCipher.newKeyBase64());
                case "enc" -> doEnc(opt, true);
                case "dec" -> doEnc(opt, false);
                default -> {
                    usage();
                    System.exit(2);
                }
            }
        } catch (Exception e) {
            System.err.println("ERROR: " + e.getMessage());
            System.exit(1);
        }
    }

    // ==================== 子命令 ====================

    private static void doSign(Map<String, String> o) {
        String appId = req(o, "appId");
        String secret = req(o, "secret");
        String method = o.getOrDefault("method", "POST");
        String path = req(o, "path");
        String kv = o.getOrDefault("keyVersion", "k1");

        CanonicalRequest cr = new CanonicalRequest(method, path);
        String query = o.get("query");
        if (query != null && !query.isBlank()) {
            cr.queryFromUrl("?" + query);
        }
        String body = o.get("body");
        if (body != null) {
            cr.body(body);
        }

        SignatureStrategy.SignResult r = HMAC.sign(cr, new SignCredentials(appId, secret, kv));
        System.out.println(r.printable());
        System.out.println("===== Headers =====");
        r.headers().forEach((k, v) -> System.out.printf("%-20s %s%n", k + ":", v));
        System.out.println();
        System.out.println("提示：把上面的 Canonical Request 与 Signature 发给 IoT 侧逐字符比对。");
        System.out.println("      规范串中的 ⏎ 表示换行符（\\n）。");
    }

    private static void doVerify(Map<String, String> o) {
        String secret = req(o, "secret");
        String canonical = req(o, "canonical");
        String signature = req(o, "signature");
        boolean ok = HMAC.verify(canonical, signature, new SignCredentials("_", secret, "k1"));
        String expected = HmacSha256Strategy.hmacSha256Hex(secret, canonical);
        System.out.println("期望签名: " + expected);
        System.out.println("实际签名: " + signature);
        System.out.println(ok ? "结果: PASS（一致）" : "结果: FAIL（不一致，请逐字符比对规范串）");
        if (!ok) {
            System.exit(1);
        }
    }

    private static void doEnc(Map<String, String> o, boolean encrypt) {
        String key = req(o, "key");
        String appId = o.getOrDefault("appId", "");
        String field = o.getOrDefault("field", "default");
        String value = req(o, "value");
        AesGcmFieldCipher c = new AesGcmFieldCipher(key, appId);
        System.out.println(encrypt ? c.encrypt(value, field) : c.decrypt(value, field));
    }

    // ==================== 自测 ====================

    static boolean selftest() {
        int pass = 0, fail = 0;
        System.out.println("==================================================");
        System.out.println(" YmdCryptoVerify · 协议 v2 自测");
        System.out.println("==================================================\n");

        // --- 1) SHA-256 空串（标准值） ---
        String emptyHash = CanonicalRequest.sha256Hex(new byte[0]);
        String expectEmpty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
        pass += check("SHA-256(\"\") 标准向量", expectEmpty, emptyHash);

        // --- 2) SHA-256("abc") 标准向量 ---
        String abcHash = CanonicalRequest.sha256Hex("abc".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        String expectAbc = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
        pass += check("SHA-256(\"abc\") 标准向量", expectAbc, abcHash);

        // --- 3) HMAC-SHA256 标准向量（RFC 4231 Test Case 2）---
        String hmac = HmacSha256Strategy.hmacSha256Hex("Jefe", "what do ya want for nothing?");
        String expectHmac = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843";
        pass += check("HMAC-SHA256 RFC4231 TC2", expectHmac, hmac);

        // --- 4) RFC3986 编码（空格必须是 %20 不是 +）---
        pass += check("RFC3986 空格编码", "a%20b", CanonicalRequest.rfc3986Encode("a b"));
        pass += check("RFC3986 中文编码", "%E4%B8%AD", CanonicalRequest.rfc3986Encode("中"));
        pass += check("RFC3986 保留字符", "a%2Fb%3Dc", CanonicalRequest.rfc3986Encode("a/b=c"));
        pass += check("RFC3986 不编码 unreserved", "aZ0-._~", CanonicalRequest.rfc3986Encode("aZ0-._~"));

        // --- 5) 规范串结构（7 行）---
        CanonicalRequest cr = new CanonicalRequest("post", "/v1/lock/open")
                .query("b", "2").query("a", "1")
                .body("{}")
                .timestamp("1700000000000").nonce("abc").keyVersion("k1");
        String canonical = cr.build();
        String[] lines = canonical.split("\n", -1);
        pass += check("规范串行数", "7", String.valueOf(lines.length));
        pass += check("规范串 METHOD 大写", "POST", lines[0]);
        pass += check("规范串 PATH", "/v1/lock/open", lines[1]);
        pass += check("规范串 QUERY 按 key 升序", "a=1&b=2", lines[2]);
        pass += check("规范串 BODY_HASH 长度", "64", String.valueOf(lines[3].length()));
        pass += check("规范串 TS", "1700000000000", lines[4]);
        pass += check("规范串 NONCE", "abc", lines[5]);
        pass += check("规范串 KEY_VERSION", "k1", lines[6]);

        // --- 6) queryFromUrl 解析与排序 ---
        CanonicalRequest cr2 = new CanonicalRequest("GET", "/x?a=1&b=2&c=%E4%B8%AD");
        pass += check("queryFromUrl 规范化", "a=1&b=2&c=%E4%B8%AD", cr2.canonicalQuery());

        // --- 7) 签名生成 + 验签往返 ---
        SignCredentials cred = new SignCredentials("app-test", "secret-test", "k1");
        CanonicalRequest cr3 = new CanonicalRequest("POST", "/v1/person/add").body("{\"a\":1}");
        SignatureStrategy.SignResult sr = HMAC.sign(cr3, cred);
        boolean vok = HMAC.verify(sr.canonicalString(), sr.signature(), cred);
        pass += check("签名/验签往返", "true", String.valueOf(vok));

        // --- 8) 篡改检测 ---
        boolean tampered = HMAC.verify(sr.canonicalString() + "x", sr.signature(), cred);
        pass += check("篡改规范串应验签失败", "false", String.valueOf(tampered));

        // --- 9) 密钥不同应失败 ---
        boolean wrongKey = HMAC.verify(sr.canonicalString(), sr.signature(),
                new SignCredentials("app-test", "other-secret", "k1"));
        pass += check("错误密钥应验签失败", "false", String.valueOf(wrongKey));

        // --- 10) nonce 唯一性 ---
        String n1 = HmacSha256Strategy.newNonce();
        String n2 = HmacSha256Strategy.newNonce();
        pass += check("nonce 长度 32", "32", String.valueOf(n1.length()));
        pass += check("nonce 不重复", "true", String.valueOf(!n1.equals(n2)));

        // --- 11) AES-256-GCM 往返 ---
        String key = AesGcmFieldCipher.newKeyBase64();
        AesGcmFieldCipher cipher = new AesGcmFieldCipher(key, "app-test");
        String plain = "110101199001011234";
        String enc = cipher.encrypt(plain, "idCard");
        String dec = cipher.decrypt(enc, "idCard");
        pass += check("AES-GCM 往返一致", plain, dec);
        pass += check("密文非明文", "true", String.valueOf(!plain.equals(enc)));
        // 每次 IV 不同 -> 密文不同
        String enc2 = cipher.encrypt(plain, "idCard");
        pass += check("同明文两次加密密文不同（随机IV）", "true", String.valueOf(!enc.equals(enc2)));

        // --- 12) AAD 绑定：换字段名应解密失败 ---
        boolean aadFail;
        try {
            cipher.decrypt(enc, "phone");
            aadFail = false;
        } catch (Exception e) {
            aadFail = true;
        }
        pass += check("AAD 字段绑定（换字段解密应失败）", "true", String.valueOf(aadFail));

        // --- 13) Base64(IV||ct||tag) 结构与长度 ---
        byte[] raw = java.util.Base64.getDecoder().decode(enc);
        pass += check("密文含 IV(12)+tag(16) 至少 28 字节", "true",
                String.valueOf(raw.length > 28));

        // --- 汇总 ---
        System.out.println();
        System.out.println("--------------------------------------------------");
        System.out.printf(" 通过 %d / 失败 %d%n", PASS_CNT, FAIL_CNT);
        if (FAIL_CNT == 0) {
            System.out.println(" 结果: ✔ 全部通过（协议 v2 实现可用）");
        } else {
            System.out.println(" 结果: ✘ 存在失败项，请检查实现");
        }
        System.out.println("--------------------------------------------------");
        return FAIL_CNT == 0;
    }

    private static int PASS_CNT = 0;
    private static int FAIL_CNT = 0;

    private static int check(String name, String expect, String actual) {
        boolean ok = expect.equals(actual);
        if (ok) {
            PASS_CNT++;
        } else {
            FAIL_CNT++;
        }
        System.out.printf("  [%s] %-42s %s%n",
                ok ? "PASS" : "FAIL", name,
                ok ? "" : ("期望=" + brief(expect) + " 实际=" + brief(actual)));
        return ok ? 1 : 0;
    }

    private static String brief(String s) {
        if (s == null) {
            return "null";
        }
        return s.length() > 40 ? s.substring(0, 40) + "..." : s;
    }

    // ==================== 参数解析 ====================

    private static Map<String, String> parseOptions(String[] args, int from) {
        Map<String, String> m = new java.util.LinkedHashMap<>();
        for (int i = from; i < args.length; i++) {
            String a = args[i];
            if (a.startsWith("--")) {
                String k = a.substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    m.put(k, args[++i]);
                } else {
                    m.put(k, "");
                }
            }
        }
        return m;
    }

    private static String req(Map<String, String> o, String k) {
        String v = o.get(k);
        if (v == null || v.isEmpty()) {
            throw new IllegalArgumentException("缺少参数 --" + k);
        }
        return v;
    }

    private static void usage() {
        System.out.println("""
YmdCryptoVerify —— IoT 协议 v2 签名/加密验证工具

  selftest                                自测（标准向量 + 往返 + 篡改检测）
  sign   --appId A --secret S --path P    生成签名头并打印规范串
         [--method POST] [--query "a=1&b=2"] [--body "{}"] [--keyVersion k1]
  verify --secret S --canonical C --signature G   校验签名
  genkey                                  生成 AES-256 密钥（Base64）
  enc    --key K --field F --value V [--appId A]  字段加密
  dec    --key K --field F --value V [--appId A]  字段解密
""");
    }
}
