# -*- coding: utf-8 -*-
"""补充 iot.legacy：YmdClient.callRaw() + YmdJsonPublic"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) 新增 YmdJsonPublic
p1 = os.path.join(BASE, r'iot\legacy\YmdJsonPublic.java')
io.open(p1, 'w', encoding='utf-8').write('''package com.yundao.bp.iot.legacy;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * IoT 响应字段提取（对外公开，供 grant 等上层模块使用）。
 *
 * <p>{@link YmdJson} 是包内工具，这里提供公开入口，避免上层依赖包私有类。
 */
public final class YmdJsonPublic {

    private YmdJsonPublic() {
    }

    /**
     * 从响应中取字段。优先在 {@code data} 对象内找，找不到再在根节点找。
     *
     * @return 字段值；不存在返回 null
     */
    public static String extract(String json, String field) {
        if (json == null || json.isBlank() || field == null) {
            return null;
        }
        JsonNode root = YmdJson.parse(json);
        JsonNode data = root.get("data");
        if (data != null && data.isObject()) {
            JsonNode v = data.get(field);
            if (v != null && !v.isNull()) {
                return v.asText();
            }
        }
        JsonNode v = root.get(field);
        return (v == null || v.isNull()) ? null : v.asText();
    }

    /** 取平台 status 字段。 */
    public static String status(String json) {
        return YmdJson.status(json);
    }

    /** 取平台 message 字段。 */
    public static String message(String json) {
        return YmdJson.message(json);
    }

    /** 是否是成功响应（status == "1"）。 */
    public static boolean success(String json) {
        return "1".equals(YmdJson.status(json));
    }
}
''')
print('  + iot/legacy/YmdJsonPublic.java')

# 2) 给 YmdClient 加 callRaw（在 callOrThrow 之后插入）
p2 = os.path.join(BASE, r'iot\legacy\YmdClient.java')
s = io.open(p2, encoding='utf-8').read()

anchor = '''    private static String brief(String s) {'''
new_method = '''    /**
     * 调用业务接口并返回<b>原始响应字符串</b>（不解密、不反序列化）。
     *
     * <p>用于上层模块（如 grant）自行处理响应，避免与 {@link YmdApiResult} 的泛型耦合。
     *
     * @param path      接口路径
     * @param bizParams 业务参数（明文，内部会加密）
     * @param decryptData 是否解密 {@code data} 字段（true 时返回的 data 已替换为明文）
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
                return "{\\"status\\":\\"1\\",\\"message\\":" + quote(YmdJson.message(resp))
                        + ",\\"data\\":" + plain + "}";
            }
        } catch (Exception ignored) {
            // 不是密文或解密失败：原样返回
        }
        return resp;
    }

    /** 便捷：调用并解密 data。 */
    public String callRaw(String path, java.util.Map<String, String> bizParams) {
        return callRaw(path, bizParams, true);
    }

    private static String quote(String s) {
        if (s == null) {
            return "null";
        }
        return "\\"" + s.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"") + "\\"";
    }

    private static String brief(String s) {'''

if anchor in s and 'public String callRaw' not in s:
    s = s.replace(anchor, new_method, 1)
    io.open(p2, 'w', encoding='utf-8').write(s)
    print('  + YmdClient.callRaw()')
elif 'public String callRaw' in s:
    print('  = YmdClient.callRaw() 已存在')
else:
    print('  ! 锚点未找到')

# 3) 确保 JsonNode 已导入
s = io.open(p2, encoding='utf-8').read()
if 'import com.fasterxml.jackson.databind.JsonNode;' not in s:
    s = s.replace('import com.fasterxml.jackson.databind.ObjectMapper;',
                  'import com.fasterxml.jackson.databind.JsonNode;\nimport com.fasterxml.jackson.databind.ObjectMapper;', 1)
    io.open(p2, 'w', encoding='utf-8').write(s)
    print('  + import JsonNode')
