package com.yundao.bp.iot.legacy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 极简 JSON 取值工具（避免为取一个字段引入复杂逻辑）。
 */
final class YmdJson {

    private static final ObjectMapper M = new ObjectMapper();

    private YmdJson() {
    }

    static JsonNode parse(String json) {
        try {
            return M.readTree(json);
        } catch (Exception e) {
            throw new YmdApiException("IoT 响应非合法 JSON: " + brief(json), e);
        }
    }

    static String extractString(String json, String field) {
        JsonNode root = parse(json);
        JsonNode data = root.get("data");
        if (data != null && data.isObject()) {
            JsonNode v = data.get(field);
            if (v != null && !v.isNull()) {
                return v.asText();
            }
        }
        return null;
    }

    static String status(String json) {
        JsonNode v = parse(json).get("status");
        return v == null ? null : v.asText();
    }

    static String message(String json) {
        JsonNode v = parse(json).get("message");
        return v == null ? null : v.asText();
    }

    /** 取 data 节点（可能是字符串密文，也可能是对象/数组）。 */
    static JsonNode dataNode(String json) {
        return parse(json).get("data");
    }

    private static String brief(String s) {
        return s == null ? "" : (s.length() > 200 ? s.substring(0, 200) + "..." : s);
    }
}
