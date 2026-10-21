package com.yundao.bp.iot.legacy;

import java.util.Map;

/**
 * HTTP 传输抽象（便于单测注入假实现，避免真实网络依赖）。
 */
public interface YmdHttpTransport {

    /**
     * 发送 JSON POST 请求。
     *
     * @param path    相对路径，如 {@code /ymd/auth-service/sys/getAccessToken}
     * @param payload 请求体（将被序列化为 JSON）
     * @return 响应体字符串
     * @throws YmdApiException 网络错误或非 2xx
     */
    String postJson(String path, Map<String, String> payload);
}
