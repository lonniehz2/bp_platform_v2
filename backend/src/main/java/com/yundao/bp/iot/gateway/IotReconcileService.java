package com.yundao.bp.iot.gateway;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevCommandMapper;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;
import com.yundao.bp.iot.gateway.entity.IotCallbackLog;
import com.yundao.bp.iot.gateway.mapper.IotCallbackLogMapper;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

/** IoT 日对账：指令执行、回调处理、表计上报覆盖。 */
@Service
public class IotReconcileService {

    private final DevCommandMapper commandMapper;
    private final IotCallbackLogMapper callbackLogMapper;
    private final DevDeviceMapper deviceMapper;
    private final FinMeterReadingMapper meterMapper;

    public IotReconcileService(DevCommandMapper commandMapper,
                               IotCallbackLogMapper callbackLogMapper,
                               DevDeviceMapper deviceMapper,
                               FinMeterReadingMapper meterMapper) {
        this.commandMapper = commandMapper;
        this.callbackLogMapper = callbackLogMapper;
        this.deviceMapper = deviceMapper;
        this.meterMapper = meterMapper;
    }

    public Map<String, Object> daily(LocalDate date) {
        LocalDate day = date == null ? LocalDate.now() : date;
        LocalDateTime start = day.atStartOfDay();
        LocalDateTime end = day.plusDays(1).atStartOfDay();

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("date", day.toString());
        out.put("generatedAt", LocalDateTime.now().toString());

        // ---------- 指令 ----------
        List<DevCommand> cmds = commandMapper.selectList(new LambdaQueryWrapper<DevCommand>()
                .ge(DevCommand::getCreateTime, start).lt(DevCommand::getCreateTime, end));
        Map<String, Integer> cmdStatus = new LinkedHashMap<>();
        List<Map<String, Object>> unacked = new ArrayList<>();
        LocalDateTime staleBefore = LocalDateTime.now().minusMinutes(10);
        int unackedTotal = 0;
        for (DevCommand c : cmds) {
            cmdStatus.merge(c.getStatus(), 1, Integer::sum);
            boolean unackedCmd = ("SENT".equals(c.getStatus()) || "PENDING".equals(c.getStatus()))
                    && c.getDispatchTime() != null
                    && c.getDispatchTime().isBefore(staleBefore);
            if (unackedCmd) {
                unackedTotal++;
            }
            if (unackedCmd && unacked.size() < 50) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("commandNo", c.getCommandNo());
                m.put("commandType", c.getCommandType());
                m.put("deviceId", c.getDeviceId());
                m.put("status", c.getStatus());
                m.put("dispatchTime", c.getDispatchTime() == null ? null
                        : c.getDispatchTime().toString());
                unacked.add(m);
            }
        }
        int success = cmdStatus.getOrDefault("SUCCESS", 0);
        Map<String, Object> command = new LinkedHashMap<>();
        command.put("total", cmds.size());
        command.put("byStatus", cmdStatus);
        command.put("successRate", cmds.isEmpty() ? 0
                : Math.round(success * 1000.0 / cmds.size()) / 10.0);
        command.put("unackedCount", unackedTotal);
        command.put("unacked", unacked);
        out.put("commands", command);

        // ---------- 回调 ----------
        List<IotCallbackLog> logs = callbackLogMapper.selectList(
                new LambdaQueryWrapper<IotCallbackLog>()
                        .ge(IotCallbackLog::getReceiveTime, start)
                        .lt(IotCallbackLog::getReceiveTime, end));
        Map<String, Map<String, Integer>> matrix = new LinkedHashMap<>();
        for (IotCallbackLog l : logs) {
            String action = l.getMsgType() == null ? "unknown" : l.getMsgType();
            String status = l.getProcessStatus() == null ? "UNKNOWN" : l.getProcessStatus();
            matrix.computeIfAbsent(action, k -> new LinkedHashMap<>())
                    .merge(status, 1, Integer::sum);
        }
        int done = 0;
        for (IotCallbackLog l : logs) {
            if ("DONE".equals(l.getProcessStatus())) {
                done++;
            }
        }
        Map<String, Object> callback = new LinkedHashMap<>();
        callback.put("total", logs.size());
        callback.put("done", done);
        callback.put("successRate", logs.isEmpty() ? 0
                : Math.round(done * 1000.0 / logs.size()) / 10.0);
        callback.put("matrix", matrix);
        out.put("callbacks", callback);

        // ---------- 表计 ----------
        List<DevDevice> meters = deviceMapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .in(DevDevice::getDeviceType, List.of("ELEC_METER", "WATER_METER", "GAS_METER",
                        "HEAT_METER", "METER"))
                .last("LIMIT 2000"));
        List<FinMeterReading> readings = meterMapper.selectList(
                new LambdaQueryWrapper<FinMeterReading>()
                        .ge(FinMeterReading::getReadDate, day)
                        .lt(FinMeterReading::getReadDate, day.plusDays(1)));
        List<String> reported = new ArrayList<>();
        for (FinMeterReading r : readings) {
            if (r.getDeviceId() != null) {
                reported.add(r.getDeviceId());
            }
        }
        List<Map<String, Object>> missing = new ArrayList<>();
        int covered = 0;
        for (DevDevice d : meters) {
            boolean has = reported.contains(d.getDeviceId());
            if (has) {
                covered++;
            } else if (missing.size() < 50) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("deviceId", d.getDeviceId());
                m.put("deviceType", d.getDeviceType());
                m.put("spaceId", d.getSpaceId());
                missing.add(m);
            }
        }
        Map<String, Object> meter = new LinkedHashMap<>();
        meter.put("expected", meters.size());
        meter.put("reported", readings.size());
        meter.put("covered", covered);
        meter.put("missingCount", meters.size() - covered);
        meter.put("coverageRate", meters.isEmpty() ? 0
                : Math.round(covered * 1000.0 / meters.size()) / 10.0);
        meter.put("missing", missing);
        out.put("meters", meter);
        return out;
    }
}
