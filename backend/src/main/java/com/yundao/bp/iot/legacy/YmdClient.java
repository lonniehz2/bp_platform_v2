package com.yundao.bp.iot.legacy;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.iot.legacy.dto.YmdLockInfo;
import java.time.Duration;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 云门道 IoT 客户端（现网 AES/MD5 协议）。
 *
 * <p><b>协议三步</b>（详见 {@code _验证/IoT对接规范-定稿.md}）：
 * <ol>
 *   <li>取 Token：{@link YmdTokenManager}（JSON + time 秒 + version 1.0.0 + MD5 sign）</li>
 *   <li>派生密钥：{@code pwd = token.substring(0,25)} → PBKDF2 → AES-128 key</li>
 *   <li>业务调用：<b>所有业务参数值 AES 加密</b>；{@code time/token/version} 明文；
 *       全部参数参与 sign；响应 {@code data} 为密文，需解密</li>
 * </ol>
 *
 * <p><b>实测易错点（已在代码中处理）</b>：
 * <ul>
 *   <li>Content-Type 必须 JSON（表单返回 415）</li>
 *   <li>{@code time} 必须秒级（毫秒失败）</li>
 *   <li>{@code version} 传 {@code 1.0.0}（传 V 前缀会变 VV）</li>
 *   <li>业务接口的 {@code appKey/appSecret} 也<b>必须加密</b>，
 *       否则分别报 99990002（缺）/ 99990010（明文）</li>
 * </ul>
 */
public class YmdClient {

    /** 获取代理商门锁清单 */
    public static final String PATH_AGENT_LOCKS = "/ymd/lockPt-service/pt/getPtAgentLocks";
    /** 获取门锁信息 */
    public static final String PATH_LOCK_INFO = "/ymd/lockPt-service/pt/getLockInfo";

    private final YmdHttpTransport transport;
    private final YmdTokenManager tokenManager;
    private final YmdCredentials credentials;
    private final boolean includeAppCredentials;
    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * @param includeAppCredentials 业务接口是否附带加密后的 appKey/appSecret。
     *                              ⚠️ 实测 {@code getPtAgentLocks} <b>需要</b>（true）。
     *                              若某些接口不需要，可传 false。
     */
    public YmdClient(YmdHttpTransport transport, YmdTokenManager tokenManager,
                     YmdCredentials credentials, boolean includeAppCredentials) {
        this.transport = transport;
        this.tokenManager = tokenManager;
        this.credentials = credentials;
        this.includeAppCredentials = includeAppCredentials;
    }

    /** 便捷构造：使用 JDK HttpClient + 默认超时。 */
    public static YmdClient create(String baseUrl, String appKey, String appSecret,
                                  boolean includeAppCredentials, boolean insecureTls) {
        JdkHttpTransport transport = new JdkHttpTransport(baseUrl,
                Duration.ofSeconds(3), Duration.ofSeconds(30), insecureTls);
        YmdCredentials cred = new YmdCredentials(appKey, appSecret, "1.0.0");
        return new YmdClient(transport, new YmdTokenManager(transport, cred), cred,
                includeAppCredentials);
    }

    public YmdToken token() {
        return tokenManager.getToken();
    }

    /**
     * 调用业务接口（所有业务参数值加密）。
     *
     * @param path      接口路径
     * @param bizParams 业务参数（明文，内部会加密）
     * @param dataType  响应 data 解密后的目标类型
     */
    public <T> YmdApiResult<T> call(String path, Map<String, String> bizParams,
                                    TypeReference<T> dataType) {
        YmdToken token = tokenManager.getToken();
        String pwd = token.pwd();

        // ---- 组装请求：业务参数全部加密 ----
        Map<String, String> payload = new LinkedHashMap<>();
        if (includeAppCredentials) {
            // ⚠️ appKey/appSecret 也必须加密，否则 99990002 / 99990010
            payload.put("appKey", AesCbcStrategy.encrypt(pwd, credentials.appKey()));
            payload.put("appSecret", AesCbcStrategy.encrypt(pwd, credentials.appSecret()));
        }
        if (bizParams != null) {
            bizParams.forEach((k, v) -> {
                if (v != null) {
                    payload.put(k, AesCbcStrategy.encrypt(pwd, v));
                }
            });
        }
        payload.put("time", String.valueOf(java.time.Instant.now().getEpochSecond()));
        payload.put("token", token.token());
        payload.put("version", credentials.version());
        payload.put("sign", Md5Signer.sign(payload));

        String resp = transport.postJson(path, payload);
        String status = YmdJson.status(resp);
        String message = YmdJson.message(resp);
        JsonNode dataNode = YmdJson.dataNode(resp);

        T data = null;
        String rawData = null;
        if (dataNode != null && !dataNode.isNull()) {
            if (dataNode.isTextual()) {
                // ⭐ 密文：需解密
                rawData = dataNode.asText();
                if ("1".equals(status)) {
                    String plain = AesCbcStrategy.decrypt(pwd, rawData);
                    data = readJson(plain, dataType);
                }
            } else {
                // 少数接口直接返回明文对象/数组
                rawData = dataNode.toString();
                if (dataType != null) {
                    data = mapper.convertValue(dataNode, dataType);
                }
            }
        }
        return new YmdApiResult<>(status, message, data, rawData);
    }

    /** 便捷：调用并断言成功。 */
    public <T> T callOrThrow(String path, Map<String, String> bizParams,
                             TypeReference<T> dataType) {
        YmdApiResult<T> r = call(path, bizParams, dataType);
        if (!r.success()) {
            throw new YmdApiException("IoT 业务失败 [" + r.status() + "] " + r.message(),
                    r.status(), 200);
        }
        return r.data();
    }

    /**
     * 调用业务接口并返回<b>原始响应字符串</b>（不反序列化）。
     *
     * <p>供上层模块（如 grant）自行处理响应，避免与 {@link YmdApiResult} 的泛型耦合。
     *
     * @param path        接口路径
     * @param bizParams   业务参数（明文，内部会加密）
     * @param decryptData 是否解密 {@code data} 字段（true 时返回的 data 已替换为明文 JSON）
     */
    public String callRaw(String path, java.util.Map<String, String> bizParams,
                          boolean decryptData) {
        YmdToken token = tokenManager.getToken();
        String pwd = token.pwd();

        Map<String, String> payload = new LinkedHashMap<>();
        if (includeAppCredentials) {
            payload.put("appKey", AesCbcStrategy.encrypt(pwd, credentials.appKey()));
            payload.put("appSecret", AesCbcStrategy.encrypt(pwd, credentials.appSecret()));
        }
        if (bizParams != null) {
            bizParams.forEach((k, v) -> {
                if (v != null) {
                    payload.put(k, AesCbcStrategy.encrypt(pwd, v));
                }
            });
        }
        payload.put("time", String.valueOf(java.time.Instant.now().getEpochSecond()));
        payload.put("token", token.token());
        payload.put("version", credentials.version());
        payload.put("sign", Md5Signer.sign(payload));

        String resp = transport.postJson(path, payload);
        if (!decryptData) {
            return resp;
        }
        // 尽力解密：失败则原样返回，交由上层判断
        try {
            JsonNode dataNode = YmdJson.dataNode(resp);
            if (dataNode != null && dataNode.isTextual() && "1".equals(YmdJson.status(resp))) {
                String plain = AesCbcStrategy.decrypt(pwd, dataNode.asText());
                return "{\"status\":\"1\",\"message\":\"操作成功\",\"data\":" + plain + "}";
            }
        } catch (Exception ignored) {
            // 非密文或解密失败：原样返回
        }
        return resp;
    }

    /** 便捷：调用并解密 data。 */
    public String callRaw(String path, java.util.Map<String, String> bizParams) {
        return callRaw(path, bizParams, true);
    }

    private <T> T readJson(String plain, TypeReference<T> type) {
        if (type == null || plain == null || plain.isBlank()) {
            return null;
        }
        try {
            return mapper.readValue(plain, type);
        } catch (Exception e) {
            throw new YmdApiException("IoT 响应解密后 JSON 解析失败", e);
        }
    }

    /** 便捷：查询代理商门锁清单。 */
    public java.util.List<YmdLockInfo> listAgentLocks(String agentCode) {
        Map<String, String> p = new HashMap<>();
        p.put("agentCode", agentCode);
        return callOrThrow(PATH_AGENT_LOCKS, p,
                new TypeReference<java.util.List<YmdLockInfo>>() { });
    }
}
