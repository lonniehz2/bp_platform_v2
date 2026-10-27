package com.yundao.bp.iot.gateway;

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

        // 端到端时延（IoT 回执 costMs）：平均 / P95 / 最大
        java.util.List<Integer> costs = new java.util.ArrayList<>();
        for (DevCommand c : cmds) {
            if (c.getCostMs() != null && c.getCostMs() >= 0) {
                costs.add(c.getCostMs());
            }
        }
        Map<String, Object> cost = new LinkedHashMap<>();
        if (costs.isEmpty()) {
            cost.put("samples", 0);
            cost.put("avgMs", null);
            cost.put("p95Ms", null);
            cost.put("maxMs", null);
        } else {
            java.util.Collections.sort(costs);
            long sum = 0;
            for (Integer v : costs) {
                sum += v;
            }
            int p95 = costs.get(Math.min(costs.size() - 1,
                    (int) Math.ceil(costs.size() * 0.95) - 1));
            cost.put("samples", costs.size());
            cost.put("avgMs", Math.round(sum * 10.0 / costs.size()) / 10.0);
            cost.put("p95Ms", p95);
            cost.put("maxMs", costs.get(costs.size() - 1));
        }
        command.put("cost", cost);
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
