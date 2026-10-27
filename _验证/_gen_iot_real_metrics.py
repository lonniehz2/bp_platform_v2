# -*- coding: utf-8 -*-
"""真实指令下发客户端 + IoT 监控指标接口 + 监控页面。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


write('dev/iot/RealDeviceCommandClient.java', '''package com.yundao.bp.dev.iot;

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
''')

write('iot/gateway/IotMetricsController.java', '''package com.yundao.bp.iot.gateway;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.dev.mapper.DevCommandMapper;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.mapper.DevEventMapper;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iot.gateway.entity.IotCallbackLog;
import com.yundao.bp.iot.gateway.entity.IotNonce;
import com.yundao.bp.iot.gateway.mapper.IotCallbackLogMapper;
import com.yundao.bp.iot.gateway.mapper.IotNonceMapper;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** IoT 监控指标：在线率、指令成功率、回调成功率、事件分布。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotMetricsController {

    private final DevDeviceMapper deviceMapper;
    private final DevCommandMapper commandMapper;
    private final DevEventMapper eventMapper;
    private final IotCallbackLogMapper callbackLogMapper;
    private final IotNonceMapper nonceMapper;

    public IotMetricsController(DevDeviceMapper deviceMapper, DevCommandMapper commandMapper,
                                DevEventMapper eventMapper, IotCallbackLogMapper callbackLogMapper,
                                IotNonceMapper nonceMapper) {
        this.deviceMapper = deviceMapper;
        this.commandMapper = commandMapper;
        this.eventMapper = eventMapper;
        this.callbackLogMapper = callbackLogMapper;
        this.nonceMapper = nonceMapper;
    }

    @RequirePerm("asset:device:view")
    @GetMapping("/metrics")
    public R<Map<String, Object>> metrics(@RequestParam(defaultValue = "24") int hours) {
        LocalDateTime since = LocalDateTime.now().minusHours(Math.max(1, hours));
        Map<String, Object> out = new LinkedHashMap<>();

        Long total = deviceMapper.selectCount(new LambdaQueryWrapper<>());
        Long online = deviceMapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1));
        Map<String, Object> dev = new LinkedHashMap<>();
        dev.put("total", total);
        dev.put("online", online);
        dev.put("offline", (total == null ? 0 : total) - (online == null ? 0 : online));
        dev.put("onlineRate", total == null || total == 0 ? 0
                : Math.round((online == null ? 0 : online) * 1000.0 / total) / 10.0);
        out.put("devices", dev);

        // 指令：近 N 小时各状态数量
        List<DevCommand> cmds = commandMapper.selectList(new LambdaQueryWrapper<DevCommand>()
                .ge(DevCommand::getCreateTime, since));
        Map<String, Integer> cmdStatus = new LinkedHashMap<>();
        int success = 0;
        for (DevCommand c : cmds) {
            cmdStatus.merge(c.getStatus(), 1, Integer::sum);
            if ("SUCCESS".equals(c.getStatus())) {
                success++;
            }
        }
        Map<String, Object> command = new LinkedHashMap<>();
        command.put("total", cmds.size());
        command.put("success", success);
        command.put("successRate", cmds.isEmpty() ? 0
                : Math.round(success * 1000.0 / cmds.size()) / 10.0);
        command.put("byStatus", cmdStatus);
        out.put("commands", command);

        // 回调：近 N 小时按处理状态
        List<IotCallbackLog> logs = callbackLogMapper.selectList(
                new LambdaQueryWrapper<IotCallbackLog>()
                        .ge(IotCallbackLog::getReceiveTime, since));
        Map<String, Integer> byStatus = new LinkedHashMap<>();
        Map<String, Integer> byAction = new LinkedHashMap<>();
        int ok = 0;
        for (IotCallbackLog l : logs) {
            byStatus.merge(l.getProcessStatus() == null ? "UNKNOWN" : l.getProcessStatus(),
                    1, Integer::sum);
            byAction.merge(l.getMsgType() == null ? "unknown" : l.getMsgType(), 1, Integer::sum);
            if ("DONE".equals(l.getProcessStatus())) {
                ok++;
            }
        }
        Map<String, Object> callback = new LinkedHashMap<>();
        callback.put("total", logs.size());
        callback.put("done", ok);
        callback.put("successRate", logs.isEmpty() ? 0
                : Math.round(ok * 1000.0 / logs.size()) / 10.0);
        callback.put("byStatus", byStatus);
        callback.put("byAction", byAction);
        out.put("callbacks", callback);

        // 事件：近 N 小时 Top 类型
        QueryWrapper<DevEvent> qw = new QueryWrapper<DevEvent>()
                .select("identifier", "count(*) as cnt")
                .ge("create_time", since)
                .groupBy("identifier")
                .orderByDesc("cnt")
                .last("LIMIT 8");
        List<Map<String, Object>> rows = eventMapper.selectMaps(qw);
        List<Map<String, Object>> top = new ArrayList<>();
        for (Map<String, Object> r : rows) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("identifier", r.get("identifier"));
            m.put("count", r.get("cnt"));
            top.add(m);
        }
        out.put("events", Map.of("total", eventMapper.selectCount(
                new LambdaQueryWrapper<DevEvent>().ge(DevEvent::getCreateTime, since)),
                "top", top));

        out.put("nonceCount", nonceMapper.selectCount(new LambdaQueryWrapper<IotNonce>()));
        out.put("generatedAt", LocalDateTime.now().toString());
        out.put("windowHours", hours);
        return R.ok(out);
    }
}
''')

print('真实客户端与指标接口完成')
