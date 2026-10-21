package com.yundao.bp.open;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.open.security.OpenSigner;
import com.yundao.bp.open.security.SecretCipher;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 开放平台：签名 / 白名单 / 密钥加密 测试。
 *
 * <p><b>为什么必须测</b>：这三处是开放平台的<b>安全边界</b>。
 * 签名错了第三方调不通；签名太松会被伪造；密钥存储不当等于所有第三方应用被接管。
 */
class OpenSignTest {

    private final OpenSigner signer = new OpenSigner();
    private final SecretCipher cipher = new SecretCipher("TEST-MASTER-KEY-32-BYTES-LONG!!");

    // ==================== 签名 ====================

    @Test
    @DisplayName("⭐ 同一输入签名稳定（第三方可复算）")
    void signStable() {
        String payload = signer.buildPayload("POST", "/open/house.list", "1700000000000",
                "abc123", "{\"page\":1}");
        String s1 = signer.sign("secret-key", payload);
        String s2 = signer.sign("secret-key", payload);
        assertEquals(s1, s2);
        assertEquals(64, s1.length(), "HMAC-SHA256 十六进制应为 64 字符");
    }

    @Test
    @DisplayName("⭐ 换密钥 → 签名不同")
    void differentSecretDiffers() {
        String payload = signer.buildPayload("POST", "/open/x", "1", "n", "b");
        assertNotEquals(signer.sign("key-a", payload), signer.sign("key-b", payload));
    }

    @Test
    @DisplayName("⭐⭐ 五个要素任一变化都改变签名（防篡改）")
    void anyFieldChangeBreaksSign() {
        String base = signer.sign("k", signer.buildPayload("POST", "/open/x", "1", "n", "b"));
        assertNotEquals(base, signer.sign("k",
                signer.buildPayload("GET", "/open/x", "1", "n", "b")), "method");
        assertNotEquals(base, signer.sign("k",
                signer.buildPayload("POST", "/open/y", "1", "n", "b")), "path");
        assertNotEquals(base, signer.sign("k",
                signer.buildPayload("POST", "/open/x", "2", "n", "b")), "timestamp");
        assertNotEquals(base, signer.sign("k",
                signer.buildPayload("POST", "/open/x", "1", "m", "b")), "nonce");
        assertNotEquals(base, signer.sign("k",
                signer.buildPayload("POST", "/open/x", "1", "n", "c")), "body");
    }

    @Test
    @DisplayName("待签串格式固定：METHOD\\nPATH\\nTS\\nNONCE\\nBODY")
    void payloadFormat() {
        assertEquals("POST\n/open/a\n123\nnn\nbody",
                signer.buildPayload("post", "/open/a", "123", "nn", "body"));
    }

    @Test
    @DisplayName("方法名自动转大写（第三方小写也能通过）")
    void methodUpperCase() {
        assertEquals(signer.buildPayload("POST", "/p", "1", "n", "b"),
                signer.buildPayload("post", "/p", "1", "n", "b"));
    }

    @Test
    @DisplayName("空值不导致 NPE")
    void nullSafePayload() {
        String p = signer.buildPayload(null, null, null, null, null);
        assertTrue(p.startsWith("\n"));
        assertEquals(p, signer.buildPayload(null, null, null, null, null));
    }

    @Test
    @DisplayName("⭐ 验签：正确通过、错误拒绝、null 拒绝")
    void verify() {
        String sig = signer.sign("k", "data");
        assertTrue(signer.verify(sig, sig));
        assertFalse(signer.verify(sig, "deadbeef"));
        assertFalse(signer.verify(null, sig));
        assertFalse(signer.verify(sig, null));
    }

    // ==================== 防重放 ====================

    @Test
    @DisplayName("⭐ 时间戳在 5 分钟窗口内通过，超出拒绝")
    void timestampWindow() {
        long now = System.currentTimeMillis();
        assertTrue(signer.freshTimestamp(now, now));
        assertTrue(signer.freshTimestamp(now - 4 * 60 * 1000, now), "4 分钟前应通过");
        assertFalse(signer.freshTimestamp(now - 6 * 60 * 1000, now), "6 分钟前应拒绝");
        assertFalse(signer.freshTimestamp(now + 6 * 60 * 1000, now), "未来 6 分钟应拒绝");
    }

    @Test
    @DisplayName("nonce 每次不同（一次性，防重放）")
    void nonceUnique() {
        assertNotEquals(signer.newNonce(), signer.newNonce());
    }

    // ==================== IP 白名单 ====================

    @Test
    @DisplayName("空白名单 = 不限制")
    void emptyWhitelistAllowsAll() {
        assertTrue(signer.ipAllowed(null, "1.2.3.4"));
        assertTrue(signer.ipAllowed("", "1.2.3.4"));
        assertTrue(signer.ipAllowed("   ", "1.2.3.4"));
    }

    @Test
    @DisplayName("⭐ 精确 IP 命中通过，不在白名单拒绝")
    void exactIp() {
        String wl = "10.0.0.1,192.168.1.5";
        assertTrue(signer.ipAllowed(wl, "10.0.0.1"));
        assertTrue(signer.ipAllowed(wl, "192.168.1.5"));
        assertFalse(signer.ipAllowed(wl, "10.0.0.2"));
    }

    @Test
    @DisplayName("⭐ 支持前缀网段：192.168.1.*")
    void prefixWildcard() {
        assertTrue(signer.ipAllowed("192.168.1.*", "192.168.1.77"));
        assertFalse(signer.ipAllowed("192.168.1.*", "192.168.2.77"));
    }

    @Test
    @DisplayName("* 放开全部（内网对接用）")
    void wildcardAll() {
        assertTrue(signer.ipAllowed("*", "8.8.8.8"));
    }

    // ==================== 密钥加密 ====================

    @Test
    @DisplayName("⭐⭐ 加密后能解密回原值（HMAC 校验需要明文）")
    void encryptDecryptRoundTrip() {
        String secret = signer.newSecret();
        String stored = cipher.encrypt(secret);
        assertNotEquals(secret, stored, "不能存明文");
        assertTrue(stored.startsWith("v1:"), stored);
        assertEquals(secret, cipher.decrypt(stored));
    }

    @Test
    @DisplayName("⭐ 同一明文两次加密密文不同（随机 IV）")
    void encryptRandomized() {
        assertNotEquals(cipher.encrypt("same"), cipher.encrypt("same"));
    }

    @Test
    @DisplayName("⭐ 密文被篡改 → 解密失败（GCM 认证标签生效）")
    void tamperDetected() {
        String stored = cipher.encrypt("original-secret");
        // 改动 Base64 中段一个字符
        String bad = stored.substring(0, stored.length() - 4)
                + (stored.endsWith("AAAA") ? "BBBB" : "ZZZZ");
        try {
            cipher.decrypt(bad);
            assertTrue(false, "篡改后应解密失败");
        } catch (IllegalStateException expected) {
            assertTrue(expected.getMessage().contains("解密失败"));
        }
    }

    @Test
    @DisplayName("⭐ 换主密钥 → 无法解密（密钥轮换需重新下发）")
    void wrongMasterKeyFails() {
        String stored = cipher.encrypt("s");
        SecretCipher other = new SecretCipher("ANOTHER-MASTER-KEY-DIFFERENT!!!");
        try {
            other.decrypt(stored);
            assertTrue(false, "换密钥应解密失败");
        } catch (IllegalStateException expected) {
            assertTrue(true);
        }
    }

    @Test
    @DisplayName("null 安全")
    void nullSafeCipher() {
        assertEquals(null, cipher.encrypt(null));
        assertEquals(null, cipher.decrypt(null));
    }

    // ==================== 跨语言契约 ====================

    /**
     * ⭐⭐ 与 Python 客户端算出的签名必须完全一致。
     *
     * <p>这个常量由 `_验证/_sig_fixture.py` 用 hmac+hashlib 独立算出。
     * 两边不一致意味着<b>所有第三方调用都会验签失败</b>，
     * 而这种错误在单元测试里发现不了，只能靠固定向量锁住。
     */
    private static final String FIXTURE_SIGN =
            "bfd8aaf613b8ebad85623b253b49e2eb7e7fa1b241412ec44a1e04e793de7f61";

    @Test
    @DisplayName("⭐⭐ 签名与 Python 客户端结果一致（跨语言契约）")
    void crossLanguageFixture() {
        String payload = signer.buildPayload("POST", "/open/house.list",
                "1700000000000", "abc123", "{\"pageNum\":1}");
        assertEquals("POST\n/open/house.list\n1700000000000\nabc123\n{\"pageNum\":1}",
                payload, "待签串格式必须与文档一致");
        assertEquals(FIXTURE_SIGN, signer.sign("unit-test-secret", payload),
                "与 Python hmac 结果不一致，第三方将全部验签失败");
    }

    @Test
    @DisplayName("生成的 AppKey / AppSecret 格式与长度")
    void keyFormats() {
        String ak = signer.newAppKey();
        String sk = signer.newSecret();
        assertTrue(ak.startsWith("AK"));
        assertEquals(2 + 24, ak.length(), ak);
        assertEquals(64, sk.length(), "32 字节 hex");
        assertNotEquals(signer.newAppKey(), signer.newAppKey());
    }
}
