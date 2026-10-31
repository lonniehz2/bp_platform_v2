package com.yundao.bp.fin.service;

import com.yundao.bp.common.exception.BizException;
import java.math.BigDecimal;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/** IoT 平台即时抄表适配器；未配置地址时由人工抄表兜底。 */
@Service
public class IotMeterClient {

    @Value("${bp.iot.read-now-url:}")
    private String readNowUrl;

    @Value("${bp.iot.token:}")
    private String token;

    public BigDecimal readNow(Long meterPointId) {
        if (readNowUrl == null || readNowUrl.isBlank()) {
            throw BizException.stateConflict("IoT read-now 接口未配置，请使用人工抄表");
        }
        try {
            String body = "{\"meterPointId\":" + meterPointId + "}";
            HttpRequest.Builder b = HttpRequest.newBuilder()
                    .uri(URI.create(readNowUrl))
                    .timeout(Duration.ofSeconds(10))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body));
            if (token != null && !token.isBlank()) {
                b.header("Authorization", "Bearer " + token);
            }
            HttpResponse<String> resp = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(5)).build()
                    .send(b.build(), HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() >= 300) {
                throw BizException.stateConflict("IoT 抄表失败：HTTP " + resp.statusCode());
            }
            com.fasterxml.jackson.databind.JsonNode root =
                    new com.fasterxml.jackson.databind.ObjectMapper().readTree(resp.body());
            com.fasterxml.jackson.databind.JsonNode data = root.has("data") ? root.get("data") : root;
            com.fasterxml.jackson.databind.JsonNode reading = data.get("reading");
            if (reading == null || reading.isNull()) {
                throw BizException.stateConflict("IoT 返回缺少读数");
            }
            return reading.decimalValue();
        } catch (BizException e) {
            throw e;
        } catch (Exception e) {
            throw BizException.stateConflict("IoT 抄表失败：" + e.getMessage());
        }
    }
}
