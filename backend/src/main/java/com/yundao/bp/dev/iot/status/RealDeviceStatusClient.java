package com.yundao.bp.dev.iot.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.dev.iot.token.IotTokenClient;
import com.yundao.bp.iot.legacy.JdkHttpTransport;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 真实批量状态：POST /ymd/restful/device/status（单批 ≤200）。 */
@Component
@ConditionalOnProperty(name = "bp.iot.status-mode", havingValue = "real")
public class RealDeviceStatusClient implements DeviceStatusClient {

    private static final Logger log = LoggerFactory.getLogger(RealDeviceStatusClient.class);
    private static final String PATH = "/ymd/restful/device/status";
    private static final int MAX_BATCH = 200;

    private final JdkHttpTransport transport;
    private final IotTokenClient tokenClient;
    private final ObjectMapper json = new ObjectMapper();

    public RealDeviceStatusClient(@Value("${ymd.iot.base-url:}") String baseUrl,
                                  IotTokenClient tokenClient) {
        this.transport = new JdkHttpTransport(baseUrl,
                Duration.ofMillis(3000), Duration.ofMillis(10000), false);
        this.tokenClient = tokenClient;
    }

    @Override
    public List<DeviceStatus> batch(List<String> lockIds) {
        List<DeviceStatus> out = new ArrayList<>();
        for (int i = 0; i < lockIds.size(); i += MAX_BATCH) {
            out.addAll(query(lockIds.subList(i, Math.min(i + MAX_BATCH, lockIds.size()))));
        }
        return out;
    }

    private List<DeviceStatus> query(List<String> ids) {
        Map<String, String> payload = new LinkedHashMap<>();
        payload.put("token", tokenClient.token().token());
        payload.put("lockIds", String.join(",", ids));
        try {
            String raw = transport.postJson(PATH, payload);
            JsonNode node = json.readTree(raw == null ? "{}" : raw);
            String code = node.path("code").asText("0");
            if (!("0".equals(code) || "SUCCESS".equalsIgnoreCase(code))) {
                throw new IllegalStateException("批量状态查询失败: "
                        + node.path("message").asText());
            }
            List<DeviceStatus> list = new ArrayList<>();
            for (JsonNode d : node.path("data")) {
                list.add(new DeviceStatus(
                        d.path("lockId").asText(),
                        d.path("online").asBoolean(false),
                        d.has("battery") ? d.path("battery").asInt() : null,
                        d.has("rssi") ? d.path("rssi").asInt() : null,
                        d.path("lastReportTime").asText(null),
                        d.path("firmware").asText(null)));
            }
            return list;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.warn("批量状态查询异常: {}", e.getMessage());
            throw new IllegalStateException("批量状态查询异常: " + e.getMessage(), e);
        }
    }
}
