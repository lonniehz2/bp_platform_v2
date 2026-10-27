package com.yundao.bp.dev.iot;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.iot.legacy.YmdClient;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/**
 * 真实指令下发：调用 IoT 平台的指令接口。
 *
 * <p>路径与参数名按 15 号文档约定；IoT 侧最终参数确认后只需改本类。
 * 未配置 ymd.iot 凭证或调用失败时返回失败结果，由状态机重试。
 */
@Component
@ConditionalOnProperty(name = "bp.dev.command-mode", havingValue = "real")
public class RealDeviceCommandClient implements DeviceCommandClient {

    private static final Logger log = LoggerFactory.getLogger(RealDeviceCommandClient.class);

    private static final String PATH_LOCK_OPEN = "/ymd/restful/lock/open";
    private static final String PATH_REBOOT = "/ymd/restful/device/reboot";
    private static final String PATH_SYNC_TIME = "/ymd/restful/device/syncTime";
    private static final String PATH_METER_SWITCH = "/ymd/restful/meter/switch";

    private final YmdClient client;
    private final ObjectMapper json = new ObjectMapper();

    public RealDeviceCommandClient(YmdClient client) {
        this.client = client;
        log.warn("设备指令使用真实 IoT 下发：参数以 15 号文档约定为准，联调时逐项核对");
    }

    @Override
    public CommandResult send(CommandRequest req) {
        String path = switch (req.commandType()) {
            case "LOCK_OPEN" -> PATH_LOCK_OPEN;
            case "DEVICE_REBOOT" -> PATH_REBOOT;
            case "DEVICE_SYNC_TIME" -> PATH_SYNC_TIME;
            case "METER_SWITCH" -> PATH_METER_SWITCH;
            default -> null;
        };
        if (path == null) {
            return CommandResult.fail("UNSUPPORTED", "不支持的指令类型: " + req.commandType());
        }
        Map<String, String> params = new HashMap<>();
        params.put("requestId", req.requestId());
        if (req.lockId() != null) {
            params.put("lockId", req.lockId());
        }
        if (req.meterNo() != null) {
            params.put("meterNo", req.meterNo());
        }
        if (req.paramsJson() != null && !req.paramsJson().isBlank()) {
            params.put("params", req.paramsJson());
        }
        try {
            String raw = client.callRaw(path, params);
            JsonNode node = json.readTree(raw == null ? "{}" : raw);
            String code = node.path("code").asText(node.path("resultCode").asText("0"));
            String message = node.path("message").asText(node.path("msg").asText(""));
            boolean ok = "0".equals(code) || "SUCCESS".equalsIgnoreCase(code)
                    || "200".equals(code);
            Integer cost = node.has("costMs") ? node.path("costMs").asInt() : null;
            if (!ok) {
                return CommandResult.fail(code, message);
            }
            return new CommandResult(true, code, message, LocalDateTime.now(), cost);
        } catch (Exception e) {
            log.error("IoT 指令调用失败 {}: {}", req.requestId(), e.getMessage());
            return CommandResult.fail("IOT_ERROR", e.getMessage());
        }
    }
}
