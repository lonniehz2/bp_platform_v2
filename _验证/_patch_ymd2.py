# -*- coding: utf-8 -*-
"""补 YmdClient.callRaw()（正确锚点）"""
import io, os

p = os.path.join(r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp',
                 r'iot\legacy\YmdClient.java')
s = io.open(p, encoding='utf-8').read()

if 'public String callRaw' in s:
    print('callRaw 已存在')
    raise SystemExit

anchor = '    private <T> T readJson(String plain, TypeReference<T> type) {'
assert anchor in s, '锚点 readJson 未找到'

new = '''    /**
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
                return "{\\"status\\":\\"1\\",\\"message\\":\\"操作成功\\",\\"data\\":" + plain + "}";
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

'''

s = s.replace(anchor, new + anchor, 1)

if 'import com.fasterxml.jackson.databind.JsonNode;' not in s:
    s = s.replace('import com.fasterxml.jackson.databind.ObjectMapper;',
                  'import com.fasterxml.jackson.databind.JsonNode;\nimport com.fasterxml.jackson.databind.ObjectMapper;', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已插入 callRaw，文件行数', len(s.split('\n')))
