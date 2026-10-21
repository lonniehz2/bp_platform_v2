package com.yundao.bp.iot.legacy;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

/**
 * 基于 JDK {@link HttpClient} 的传输实现（零额外依赖）。
 *
 * <p>关键点（实测确认）：
 * <ul>
 *   <li>Content-Type <b>必须</b> {@code application/json}（用表单编码返回 415）</li>
 *   <li>平台证书为自签名，需允许不校验（生产建议导入信任库后关闭此开关）</li>
 * </ul>
 */
public class JdkHttpTransport implements YmdHttpTransport {

    private final HttpClient http;
    private final String baseUrl;
    private final ObjectMapper mapper = new ObjectMapper();
    private final boolean insecureTls;

    public JdkHttpTransport(String baseUrl, Duration connectTimeout, Duration requestTimeout,
                            boolean insecureTls) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.insecureTls = insecureTls;
        HttpClient.Builder b = HttpClient.newBuilder()
                .connectTimeout(connectTimeout)
                .version(HttpClient.Version.HTTP_1_1);
        if (insecureTls) {
            b.sslContext(InsecureSsl.context());
        }
        this.http = b.build();
        this.requestTimeout = requestTimeout;
    }

    private final Duration requestTimeout;

    @Override
    public String postJson(String path, Map<String, String> payload) {
        try {
            String body = mapper.writeValueAsString(payload);
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + path))
                    .timeout(requestTimeout)
                    .header("Content-Type", "application/json;charset=UTF-8")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body, java.nio.charset.StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> resp = http.send(req,
                    HttpResponse.BodyHandlers.ofString(java.nio.charset.StandardCharsets.UTF_8));
            if (resp.statusCode() < 200 || resp.statusCode() >= 300) {
                throw new YmdApiException("IoT HTTP " + resp.statusCode() + ": " + brief(resp.body()),
                        null, resp.statusCode());
            }
            return resp.body();
        } catch (YmdApiException e) {
            throw e;
        } catch (Exception e) {
            throw new YmdApiException("IoT 请求失败: " + path, e);
        }
    }

    private String brief(String s) {
        return s == null ? "" : (s.length() > 300 ? s.substring(0, 300) + "..." : s);
    }
}
