package com.yundao.bp.iot.sign;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 协议 v2 签名与字段加密单元测试。
 *
 * <p>覆盖三类：
 * <ol>
 *   <li><b>标准向量</b>：SHA-256 / HMAC-SHA256 用 RFC 公开向量，确保算法实现正确</li>
 *   <li><b>规范串</b>：结构、排序、编码规则</li>
 *   <li><b>安全性质</b>：篡改检测、错误密钥、AAD 绑定、随机 IV</li>
 * </ol>
 */
class SignatureProtocolTest {

    private final HmacSha256Strategy strategy = new HmacSha256Strategy();
    private final SignCredentials cred = new SignCredentials("app-test", "secret-test", "k1");

    // ==================== 标准向量 ====================

    @Test
    @DisplayName("SHA-256 标准向量：空串")
    void sha256Empty() {
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                CanonicalRequest.sha256Hex(new byte[0]));
    }

    @Test
    @DisplayName("SHA-256 标准向量：abc")
    void sha256Abc() {
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                CanonicalRequest.sha256Hex("abc".getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    @DisplayName("HMAC-SHA256 标准向量：RFC 4231 Test Case 2")
    void hmacRfc4231() {
        assertEquals("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843",
                HmacSha256Strategy.hmacSha256Hex("Jefe", "what do ya want for nothing?"));
    }

    // ==================== RFC3986 编码 ====================

    @Test
    @DisplayName("RFC3986：空格编码为 %20 而非 +")
    void encodeSpace() {
        assertEquals("a%20b", CanonicalRequest.rfc3986Encode("a b"));
    }

    @Test
    @DisplayName("RFC3986：中文按 UTF-8 百分号编码")
    void encodeChinese() {
        assertEquals("%E4%B8%AD", CanonicalRequest.rfc3986Encode("中"));
    }

    @Test
    @DisplayName("RFC3986：保留字符需编码")
    void encodeReserved() {
        assertEquals("a%2Fb%3Dc%26d", CanonicalRequest.rfc3986Encode("a/b=c&d"));
    }

    @Test
    @DisplayName("RFC3986：unreserved 不编码")
    void encodeUnreserved() {
        assertEquals("aZ0-._~", CanonicalRequest.rfc3986Encode("aZ0-._~"));
    }

    // ==================== 规范串 ====================

    @Test
    @DisplayName("规范串为 7 行且顺序正确")
    void canonicalStructure() {
        String canonical = new CanonicalRequest("post", "/v1/lock/open")
                .query("b", "2").query("a", "1")
                .body("{}")
                .timestamp("1700000000000").nonce("abc").keyVersion("k1")
                .build();
        String[] lines = canonical.split("\n", -1);
        assertEquals(7, lines.length);
        assertEquals("POST", lines[0], "METHOD 必须大写");
        assertEquals("/v1/lock/open", lines[1]);
        assertEquals("a=1&b=2", lines[2], "query 必须按 key 升序");
        assertEquals(64, lines[3].length(), "body hash 为 64 位十六进制");
        assertEquals("1700000000000", lines[4]);
        assertEquals("abc", lines[5]);
        assertEquals("k1", lines[6]);
    }

    @Test
    @DisplayName("path 中的 ?query 会被自动拆出并参与签名")
    void queryAutoParsed() {
        CanonicalRequest cr = new CanonicalRequest("GET", "/x?a=1&b=2&c=%E4%B8%AD");
        assertEquals("a=1&b=2&c=%E4%B8%AD", cr.canonicalQuery());
    }

    @Test
    @DisplayName("空 body 使用空串的 SHA-256")
    void emptyBodyHash() {
        CanonicalRequest cr = new CanonicalRequest("GET", "/x");
        String canonical = cr.timestamp("1").nonce("n").keyVersion("k1").build();
        String[] lines = canonical.split("\n", -1);
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", lines[3]);
    }

    // ==================== 签名与验签 ====================

    @Test
    @DisplayName("签名后可用同一凭证验签通过")
    void signAndVerify() {
        CanonicalRequest cr = new CanonicalRequest("POST", "/v1/person/add").body("{\"a\":1}");
        SignatureStrategy.SignResult sr = strategy.sign(cr, cred);

        assertTrue(strategy.verify(sr.canonicalString(), sr.signature(), cred));
        assertEquals(64, sr.signature().length());
        assertEquals(HmacSha256Strategy.PROTO, strategy.protocolVersion());
    }

    @Test
    @DisplayName("请求头包含全部必需字段")
    void headersComplete() {
        CanonicalRequest cr = new CanonicalRequest("POST", "/v1/x");
        Map<String, String> h = strategy.buildHeaders(cr, cred);

        assertTrue(h.containsKey(HmacSha256Strategy.HDR_APP_ID));
        assertTrue(h.containsKey(HmacSha256Strategy.HDR_TIMESTAMP));
        assertTrue(h.containsKey(HmacSha256Strategy.HDR_NONCE));
        assertTrue(h.containsKey(HmacSha256Strategy.HDR_KEY_VER));
        assertTrue(h.containsKey(HmacSha256Strategy.HDR_SIGNATURE));
        assertEquals(HmacSha256Strategy.PROTO, h.get(HmacSha256Strategy.HDR_PROTO));
        assertEquals(32, h.get(HmacSha256Strategy.HDR_NONCE).length());
    }

    @Test
    @DisplayName("篡改规范串后验签失败")
    void tamperedCanonicalFails() {
        CanonicalRequest cr = new CanonicalRequest("POST", "/v1/x").body("{}");
        SignatureStrategy.SignResult sr = strategy.sign(cr, cred);

        assertFalse(strategy.verify(sr.canonicalString() + "x", sr.signature(), cred));
    }

    @Test
    @DisplayName("使用错误密钥验签失败")
    void wrongSecretFails() {
        CanonicalRequest cr = new CanonicalRequest("POST", "/v1/x");
        SignatureStrategy.SignResult sr = strategy.sign(cr, cred);

        SignCredentials other = new SignCredentials("app-test", "other-secret", "k1");
        assertFalse(strategy.verify(sr.canonicalString(), sr.signature(), other));
    }

    @Test
    @DisplayName("同一请求两次签名的 nonce 与签名不同")
    void nonceIsRandom() {
        SignatureStrategy.SignResult a = strategy.sign(new CanonicalRequest("GET", "/x"), cred);
        SignatureStrategy.SignResult b = strategy.sign(new CanonicalRequest("GET", "/x"), cred);

        assertNotEquals(a.headers().get(HmacSha256Strategy.HDR_NONCE),
                b.headers().get(HmacSha256Strategy.HDR_NONCE));
        assertNotEquals(a.signature(), b.signature());
    }

    @Test
    @DisplayName("凭证 toString 不泄露 secret")
    void credentialsNotLeakSecret() {
        assertFalse(cred.toString().contains("secret-test"));
        assertTrue(cred.toString().contains("***"));
    }

    // ==================== 字段加密 ====================

    @Test
    @DisplayName("AES-GCM 加解密往返一致")
    void fieldCryptoRoundTrip() {
        AesGcmFieldCipher c = new AesGcmFieldCipher(AesGcmFieldCipher.newKeyBase64(), "app");
        String plain = "110101199001011234";
        String enc = c.encrypt(plain, "idCard");

        assertNotEquals(plain, enc, "密文不应等于明文");
        assertEquals(plain, c.decrypt(enc, "idCard"));
    }

    @Test
    @DisplayName("同明文两次加密密文不同（随机 IV）")
    void randomIv() {
        AesGcmFieldCipher c = new AesGcmFieldCipher(AesGcmFieldCipher.newKeyBase64(), "app");
        assertNotEquals(c.encrypt("x", "f"), c.encrypt("x", "f"));
    }

    @Test
    @DisplayName("AAD 绑定字段名：换字段解密必须失败")
    void aadBindsFieldName() {
        AesGcmFieldCipher c = new AesGcmFieldCipher(AesGcmFieldCipher.newKeyBase64(), "app");
        String enc = c.encrypt("110101199001011234", "idCard");

        assertThrows(IllegalStateException.class, () -> c.decrypt(enc, "phone"));
    }

    @Test
    @DisplayName("AAD 绑定 appId：换 appId 解密失败")
    void aadBindsAppId() {
        String key = AesGcmFieldCipher.newKeyBase64();
        AesGcmFieldCipher a = new AesGcmFieldCipher(key, "app-A");
        AesGcmFieldCipher b = new AesGcmFieldCipher(key, "app-B");
        String enc = a.encrypt("v", "f");

        assertThrows(IllegalStateException.class, () -> b.decrypt(enc, "f"));
    }

    @Test
    @DisplayName("密文携带 IV(12)+tag(16)，长度足够")
    void cipherLayout() {
        AesGcmFieldCipher c = new AesGcmFieldCipher(AesGcmFieldCipher.newKeyBase64(), "app");
        byte[] raw = java.util.Base64.getDecoder().decode(c.encrypt("abc", "f"));
        assertTrue(raw.length > 28, "应至少 12(IV)+3(ct)+16(tag)=31 字节");
    }

    @Test
    @DisplayName("密钥长度非 32 字节应拒绝")
    void keyLengthValidated() {
        String bad = java.util.Base64.getEncoder().encodeToString(new byte[16]);
        assertThrows(IllegalArgumentException.class, () -> new AesGcmFieldCipher(bad, "app"));
    }
}
