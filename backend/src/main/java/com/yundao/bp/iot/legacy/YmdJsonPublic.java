package com.yundao.bp.iot.legacy;

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
