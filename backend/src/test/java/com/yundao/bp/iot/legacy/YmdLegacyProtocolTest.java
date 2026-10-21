package com.yundao.bp.iot.legacy;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.type.TypeReference;
import com.yundao.bp.iot.legacy.dto.YmdLockInfo;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 现网协议（AES/MD5）测试。
 *
 * <p>三类覆盖：
 * <ol>
 *   <li><b>官方文档示例</b>：AES 与 MD5 必须与文档给的值逐字符一致</li>
 *   <li><b>协议语义</b>：加密范围、签名顺序、token 的 pwd 截取</li>
 *   <li><b>端到端（假传输）</b>：token → 加密 → 签名 → 响应解密 → DTO 映射</li>
 * </ol>
 */
class YmdLegacyProtocolTest {

    // ==================== 1. 官方文档示例（决定性验证）====================

    @Test
    @DisplayName("AES 与官方文档示例完全一致（PBKDF2 + CBC + 固定IV）")
    void aesMatchesOfficialExample() {
        // 文档 §3.3：
        //   pwd   = token.substring(0,25) = "5x41nO+EIYENqlj8FmG2XGXMa"
        //   明文  = "719B29DB1EF45F00D9C5CD320DAE6"
        //   密文  = "FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo="
        String pwd = "5x41nO+EIYENqlj8FmG2XGXMa";
        String plain = "719B29DB1EF45F00D9C5CD320DAE6";
        String expected = "FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo=";

        assertEquals(expected, AesCbcStrategy.encrypt(pwd, plain),
                "AES 加密结果必须与官方文档示例一致");
        assertEquals(plain, AesCbcStrategy.decrypt(pwd, expected),
                "解密必须还原明文");
    }

    @Test
    @DisplayName("MD5 签名与官方文档示例完全一致")
    void md5MatchesOfficialExample() {
        // 文档 §3.4：
        //   loginname=t4nU902RvhliiPlMMcrzWw==&logpwd=oFbqQ8bx8KvkHCI/Q2Kaxw==&time=1553595995&version=1.0.0
        //   → 46812299FB1BC111AC69A27F99068BE2
        Map<String, String> p = new HashMap<>();
        p.put("loginname", "t4nU902RvhliiPlMMcrzWw==");
        p.put("logpwd", "oFbqQ8bx8KvkHCI/Q2Kaxw==");
        p.put("time", "1553595995");
        p.put("version", "1.0.0");

        assertEquals("46812299FB1BC111AC69A27F99068BE2", Md5Signer.sign(p),
                "签名必须与官方文档示例一致");
    }

    @Test
    @DisplayName("签名为大写十六进制且排除 sign 自身")
    void signFormatAndExclusion() {
        Map<String, String> p = new HashMap<>();
        p.put("b", "2");
        p.put("a", "1");
        // 字典序：a=1&b=2
        String expected = Md5Signer.md5Upper("a=1&b=2");
        assertEquals(expected, Md5Signer.sign(p));
        assertEquals(expected.toUpperCase(), Md5Signer.sign(p));

        // 带 sign 时结果不变（被排除）
        Map<String, String> p2 = new HashMap<>(p);
        p2.put("sign", "SHOULD_BE_IGNORED");
        assertEquals(expected, Md5Signer.sign(p2));
    }

    // ==================== 2. 协议语义 ====================

    @Test
    @DisplayName("token 的 pwd 规定为前 25 位")
    void tokenPwdIsFirst25() {
        String tok = "U9uzhll2owQ6dTAekDQXJkJBhah26KuAb/chNmtO8EbKVtL0U37z8";
        YmdToken t = new YmdToken(tok, Instant.now(), Instant.now().plusSeconds(1800));
        assertEquals(tok.substring(0, 25), t.pwd());
        assertEquals(25, t.pwd().length());
    }

    @Test
    @DisplayName("token 过短应拒绝（无法派生密钥）")
    void tokenTooShortRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> new YmdToken("short", Instant.now(), Instant.now()));
    }

    @Test
    @DisplayName("version 必须规范为 1.0.0（传 V 前缀会导致 VV）")
    void versionNormalized() {
        // 默认构造给 1.0.0
        YmdCredentials c = new YmdCredentials("k", "s", null);
        assertEquals("1.0.0", c.version());
        // 显式传 V1.0.0 时原样保留（由调用方保证不传 V）
        assertEquals("V1.0.0", new YmdCredentials("k", "s", "V1.0.0").version());
    }

    @Test
    @DisplayName("凭证 toString 不泄露 appSecret")
    void credentialsMasked() {
        YmdCredentials c = new YmdCredentials("myKey", "super-secret-value", "1.0.0");
        assertFalse(c.toString().contains("super-secret-value"));
        assertTrue(c.toString().contains("***"));
    }

    @Test
    @DisplayName("密钥派生稳定且为 16 字节")
    void keyDerivationStable() {
        byte[] k1 = AesCbcStrategy.deriveKeyBytes("5x41nO+EIYENqlj8FmG2XGXMa");
        byte[] k2 = AesCbcStrategy.deriveKeyBytes("5x41nO+EIYENqlj8FmG2XGXMa");
        assertEquals(16, k1.length);
        assertEquals(java.util.HexFormat.of().formatHex(k1),
                java.util.HexFormat.of().formatHex(k2));
        // 与 Python 实现对比过的期望值
        assertEquals("3FA50AED662483A899B22A4BDBF7DE26",
                java.util.HexFormat.of().withUpperCase().formatHex(k1));
    }

    @Test
    @DisplayName("不同口令派生不同密钥")
    void differentPwdDifferentKey() {
        String a = java.util.HexFormat.of().formatHex(
                AesCbcStrategy.deriveKeyBytes("AAAAAAAAAAAAAAAAAAAAAAAAA"));
        String b = java.util.HexFormat.of().formatHex(
                AesCbcStrategy.deriveKeyBytes("BBBBBBBBBBBBBBBBBBBBBBBBB"));
        assertFalse(a.equals(b));
    }

    @Test
    @DisplayName("解密容忍密文中的空白字符（平台返回可能带换行）")
    void decryptToleratesWhitespace() {
        String pwd = "5x41nO+EIYENqlj8FmG2XGXMa";
        String ct = AesCbcStrategy.encrypt(pwd, "hello");
        String messy = ct.substring(0, 8) + "\n " + ct.substring(8);
        assertEquals("hello", AesCbcStrategy.decrypt(pwd, messy));
    }

    @Test
    @DisplayName("错误密钥解密应抛异常")
    void wrongKeyFailsToDecrypt() {
        String ct = AesCbcStrategy.encrypt("5x41nO+EIYENqlj8FmG2XGXMa", "data");
        assertThrows(IllegalStateException.class,
                () -> AesCbcStrategy.decrypt("ZZZZZZZZZZZZZZZZZZZZZZZZZ", ct));
    }

    @Test
    @DisplayName("空口令与空入参的边界处理")
    void boundaryCases() {
        assertThrows(IllegalArgumentException.class, () -> AesCbcStrategy.deriveKey(""));
        assertThrows(IllegalArgumentException.class, () -> AesCbcStrategy.deriveKey(null));
        assertNull(AesCbcStrategy.encrypt("k".repeat(25), null));
        assertNull(AesCbcStrategy.decrypt("k".repeat(25), null));
    }

    // ==================== 3. 端到端（假传输）====================

    /** 假传输：记录请求，按需返回预置响应 */
    static class FakeTransport implements YmdHttpTransport {
        final List<Map<String, String>> requests = new ArrayList<>();
        final Map<String, String> responses = new HashMap<>();
        final AtomicInteger tokenCalls = new AtomicInteger();

        @Override
        public String postJson(String path, Map<String, String> payload) {
            requests.add(new HashMap<>(payload));
            if (YmdTokenManager.TOKEN_PATH.equals(path)) {
                tokenCalls.incrementAndGet();
            }
            String r = responses.get(path);
            if (r == null) {
                throw new YmdApiException("no response for " + path, null, -1);
            }
            return r;
        }
    }

    private static final String PWD = "U9uzhll2owQ6dTAekDQXJkJBh";
    private static final String TOKEN = PWD + "EXTRA_TOKEN_SUFFIX_FOR_TEST";

    private YmdClient newClient(FakeTransport t, YmdCredentials cred) {
        YmdTokenManager tm = new YmdTokenManager(t, cred, Duration.ofMinutes(30), Duration.ofMinutes(5));
        return new YmdClient(t, tm, cred, true);
    }

    @Test
    @DisplayName("端到端：取 token → 参数加密 → 签名 → 响应解密 → DTO 映射")
    void endToEndWithFakeTransport() {
        FakeTransport t = new FakeTransport();
        YmdCredentials cred = new YmdCredentials("APPKEY_TEST", "APPSECRET_TEST", "1.0.0");

        // 1) token 响应
        t.responses.put(YmdTokenManager.TOKEN_PATH,
                "{\"status\":\"1\",\"message\":\"操作成功\",\"data\":{\"token\":\"" + TOKEN + "\"}}");

        // 2) 业务响应：真实平台返回的 data 是 AES 密文
        String plainData = "[{\"lockid\":\"LK001\",\"mac\":\"MAC001\",\"lockname\":\"101室\","
                + "\"onlineStatus\":\"1\",\"battery\":\"86%\",\"ventor\":\"485A4254\"}]";
        String encrypted = AesCbcStrategy.encrypt(PWD, plainData);
        t.responses.put(YmdClient.PATH_AGENT_LOCKS,
                "{\"status\":\"1\",\"message\":\"操作成功\",\"data\":\"" + encrypted + "\"}");

        YmdClient client = newClient(t, cred);
        List<YmdLockInfo> locks = client.listAgentLocks("20261019001");

        // --- 断言：token 请求正确 ---
        Map<String, String> tokenReq = t.requests.get(0);
        assertEquals(1, t.tokenCalls.get());
        assertEquals("APPKEY_TEST", tokenReq.get("appKey"));
        assertEquals("APPSECRET_TEST", tokenReq.get("appSecret"));
        assertEquals("1.0.0", tokenReq.get("version"));
        assertEquals(10, tokenReq.get("time").length(), "time 必须是秒级（10 位）");
        assertEquals(Md5Signer.sign(tokenReq), tokenReq.get("sign"), "token 请求签名须自洽");

        // --- 断言：业务请求参数全部加密 ---
        Map<String, String> bizReq = t.requests.get(1);
        assertEquals(AesCbcStrategy.encrypt(PWD, "APPKEY_TEST"), bizReq.get("appKey"),
                "appKey 必须加密");
        assertEquals(AesCbcStrategy.encrypt(PWD, "APPSECRET_TEST"), bizReq.get("appSecret"),
                "appSecret 必须加密");
        assertEquals(AesCbcStrategy.encrypt(PWD, "20261019001"), bizReq.get("agentCode"),
                "agentCode 必须加密");
        assertEquals(TOKEN, bizReq.get("token"), "token 保持明文");
        assertEquals("1.0.0", bizReq.get("version"));
        assertEquals(10, bizReq.get("time").length());
        assertEquals(Md5Signer.sign(bizReq), bizReq.get("sign"), "业务签名须自洽");

        // --- 断言：响应解密与映射 ---
        assertEquals(1, locks.size());
        YmdLockInfo lock = locks.get(0);
        assertEquals("LK001", lock.getLockId());
        assertEquals("101室", lock.getLockName());
        assertTrue(lock.online(), "onlineStatus=1 应判定为在线");
        assertEquals(86, lock.batteryPercent());
    }

    @Test
    @DisplayName("业务失败（status != 1）应抛异常并带平台状态码")
    void businessFailureThrows() {
        FakeTransport t = new FakeTransport();
        YmdCredentials cred = new YmdCredentials("K", "S", "1.0.0");
        t.responses.put(YmdTokenManager.TOKEN_PATH,
                "{\"status\":\"1\",\"data\":{\"token\":\"" + TOKEN + "\"}}");
        // 实测典型失败：明文 appKey → 99990010
        t.responses.put(YmdClient.PATH_AGENT_LOCKS,
                "{\"message\":\"appKey参数解密异常\",\"status\":\"99990010\"}");

        YmdClient client = newClient(t, cred);
        YmdApiException ex = assertThrows(YmdApiException.class,
                () -> client.listAgentLocks("A1"));
        assertEquals("99990010", ex.status());
        assertTrue(ex.getMessage().contains("99990010"));
    }

    @Test
    @DisplayName("token 缓存：有效期内只取一次")
    void tokenCached() {
        FakeTransport t = new FakeTransport();
        YmdCredentials cred = new YmdCredentials("K", "S", "1.0.0");
        t.responses.put(YmdTokenManager.TOKEN_PATH,
                "{\"status\":\"1\",\"data\":{\"token\":\"" + TOKEN + "\"}}");
        String enc = AesCbcStrategy.encrypt(PWD, "[]");
        t.responses.put(YmdClient.PATH_AGENT_LOCKS,
                "{\"status\":\"1\",\"data\":\"" + enc + "\"}");

        YmdClient client = newClient(t, cred);
        client.listAgentLocks("A");
        client.listAgentLocks("A");
        client.listAgentLocks("A");
        assertEquals(1, t.tokenCalls.get(), "3 次业务调用应只取 1 次 token");
    }

    @Test
    @DisplayName("token 临近过期（<5 分钟）应自动续期")
    void tokenRenewsWhenExpiring() {
        FakeTransport t = new FakeTransport();
        YmdCredentials cred = new YmdCredentials("K", "S", "1.0.0");
        t.responses.put(YmdTokenManager.TOKEN_PATH,
                "{\"status\":\"1\",\"data\":{\"token\":\"" + TOKEN + "\"}}");

        // 构造一个 ttl=1 分钟、提前 5 分钟续期的管理器 → 每次都续期
        YmdTokenManager tm = new YmdTokenManager(t, cred,
                Duration.ofMinutes(1), Duration.ofMinutes(5));
        tm.getToken();
        tm.getToken();
        assertEquals(2, t.tokenCalls.get(), "临近过期应每次续期");
    }

    @Test
    @DisplayName("响应 data 为明文对象时也能解析（兼容少数接口）")
    void plainTextDataSupported() {
        FakeTransport t = new FakeTransport();
        YmdCredentials cred = new YmdCredentials("K", "S", "1.0.0");
        t.responses.put(YmdTokenManager.TOKEN_PATH,
                "{\"status\":\"1\",\"data\":{\"token\":\"" + TOKEN + "\"}}");
        t.responses.put(YmdClient.PATH_AGENT_LOCKS,
                "{\"status\":\"1\",\"data\":[{\"lockid\":\"X\",\"onlineStatus\":\"0\"}]}");

        YmdClient client = newClient(t, cred);
        List<YmdLockInfo> locks = client.listAgentLocks("A");
        assertEquals(1, locks.size());
        assertFalse(locks.get(0).online());
        assertNull(locks.get(0).batteryPercent(), "无电量信息应返回 null");
    }

    @Test
    @DisplayName("YmdLockInfo 电量解析容错")
    void batteryParsing() {
        YmdLockInfo l = new YmdLockInfo();
        l.setBattery("43%");
        assertEquals(43, l.batteryPercent());
        l.setBattery("100%");
        assertEquals(100, l.batteryPercent());
        l.setBattery(null);
        assertNull(l.batteryPercent());
        l.setBattery("abc");
        assertNull(l.batteryPercent());
    }
}
