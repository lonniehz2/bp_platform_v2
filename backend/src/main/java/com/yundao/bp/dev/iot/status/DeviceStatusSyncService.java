package com.yundao.bp.dev.iot.status;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/** 把 IoT 批量状态回写到设备表（在线/电量/最后上报）。 */
@Service
public class DeviceStatusSyncService {

    private static final Logger log = LoggerFactory.getLogger(DeviceStatusSyncService.class);
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final DeviceStatusClient client;
    private final DevDeviceMapper mapper;

    public DeviceStatusSyncService(DeviceStatusClient client, DevDeviceMapper mapper) {
        this.client = client;
        this.mapper = mapper;
    }

    /** @param lockIds 指定设备编号；为空则取前 limit 台 */
    public Map<String, Object> sync(List<String> lockIds, int limit) {
        List<DevDevice> devices;
        if (lockIds != null && !lockIds.isEmpty()) {
            devices = mapper.selectList(new LambdaQueryWrapper<DevDevice>()
                    .in(DevDevice::getDeviceId, lockIds));
        } else {
            int cap = Math.max(1, Math.min(limit, 500));
            devices = mapper.selectList(new LambdaQueryWrapper<DevDevice>()
                    .last("LIMIT " + cap));
        }
        if (devices.isEmpty()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("requested", 0);
            empty.put("updated", 0);
            empty.put("online", 0);
            empty.put("offline", 0);
            empty.put("unknown", 0);
            return empty;
        }
        List<String> ids = new ArrayList<>();
        Map<String, DevDevice> byLock = new LinkedHashMap<>();
        for (DevDevice d : devices) {
            if (d.getDeviceId() != null) {
                ids.add(d.getDeviceId());
                byLock.put(d.getDeviceId(), d);
            }
        }
        List<DeviceStatusClient.DeviceStatus> statuses = client.batch(ids);
        int updated = 0;
        int online = 0;
        int offline = 0;
        int unknown = 0;
        for (DeviceStatusClient.DeviceStatus s : statuses) {
            DevDevice d = byLock.get(s.lockId());
            if (d == null) {
                unknown++;
                continue;
            }
            d.setOnlineStatus(s.online() ? 1 : 0);
            if (s.battery() != null) {
                d.setBattery(s.battery());
            }
            d.setLastReportTime(parse(s.lastReportTime()));
            d.setUpdateTime(LocalDateTime.now());
            mapper.updateById(d);
            updated++;
            if (s.online()) {
                online++;
            } else {
                offline++;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("requested", ids.size());
        out.put("updated", updated);
        out.put("online", online);
        out.put("offline", offline);
        out.put("unknown", unknown);
        log.info("批量状态同步：请求 {} 台，更新 {}（在线 {} / 离线 {}），未匹配 {}",
                ids.size(), updated, online, offline, unknown);
        return out;
    }

    private static LocalDateTime parse(String text) {
        if (text == null || text.isBlank()) {
            return LocalDateTime.now();
        }
        try {
            return LocalDateTime.parse(text.replace('T', ' '), FMT);
        } catch (Exception e) {
            return LocalDateTime.now();
        }
    }
}
