# -*- coding: utf-8 -*-
"""心跳单条 UPDATE + 连接池上调，提升回调吞吐。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

p = os.path.join(BE, 'iot', 'gateway', 'IotCallbackService.java')
s = io.open(p, encoding='utf-8').read()
old = '''            LocalDateTime now = LocalDateTime.now();
        for (JsonNode x : items) {'''
if 'updateHeartbeat' not in s:
    s = s.replace('''        LocalDateTime now = LocalDateTime.now();
        for (JsonNode x : items) {
            DevDevice d = findDevice(text(x, "deviceId"), text(x, "lockId"));
            if (d == null) {
                continue;
            }
            boolean online = x.path("online").asBoolean(true);
            d.setOnlineStatus(online ? 1 : 0);
            if (online) {
                d.setOnlineTime(now);
            } else {
                d.setOfflineTime(now);
            }
            Integer battery = intVal(x, "battery", null);
            if (battery != null) {
                d.setBattery(battery);
            }
            String rssi = text(x, "rssi");
            if (rssi != null) {
                d.setRssi(rssi);
            }
            d.setLastReportTime(parseTime(text(x, "reportTime")) == null
                    ? now : parseTime(text(x, "reportTime")));
            d.setUpdateTime(now);
            deviceMapper.updateById(d);
        }
    }''', '''        LocalDateTime now = LocalDateTime.now();
        for (JsonNode x : items) {
            // 单条 UPDATE，避免「查一次 + 改一次」两倍往返
            String deviceId = text(x, "deviceId");
            String lockId = text(x, "lockId");
            boolean online = x.path("online").asBoolean(true);
            Integer battery = intVal(x, "battery", null);
            LocalDateTime reportTime = parseTime(text(x, "reportTime"));
            int updated = updateHeartbeat(deviceId, lockId, online, battery,
                    text(x, "rssi"), reportTime == null ? now : reportTime, now);
            if (updated == 0) {
                log.debug("心跳设备不存在 device={} lock={}", deviceId, lockId);
            }
        }
    }

    private int updateHeartbeat(String deviceId, String lockId, boolean online,
                                Integer battery, String rssi,
                                LocalDateTime reportTime, LocalDateTime now) {
        com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper<DevDevice> uw =
                new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper<DevDevice>()
                        .set(DevDevice::getOnlineStatus, online ? 1 : 0)
                        .set(DevDevice::getLastReportTime, reportTime)
                        .set(DevDevice::getUpdateTime, now);
        if (online) {
            uw.set(DevDevice::getOnlineTime, now);
        } else {
            uw.set(DevDevice::getOfflineTime, now);
        }
        if (battery != null) {
            uw.set(DevDevice::getBattery, battery);
        }
        if (rssi != null) {
            uw.set(DevDevice::getRssi, rssi);
        }
        if (deviceId != null && !deviceId.isBlank()) {
            int n = deviceMapper.update(null, uw.eq(DevDevice::getDeviceId, deviceId));
            if (n > 0 || lockId == null || lockId.isBlank()) {
                return n;
            }
        }
        if (lockId != null && !lockId.isBlank()) {
            return deviceMapper.update(null,
                    uw.eq(DevDevice::getDeviceId, lockId));
        }
        return 0;
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('心跳已改单条 UPDATE')

p = os.path.join(ROOT, 'backend', 'src', 'main', 'resources', 'application.yml')
s = io.open(p, encoding='utf-8').read()
if 'maximum-pool-size: 20' in s:
    s = s.replace('maximum-pool-size: 20', 'maximum-pool-size: 40')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('连接池已调到 40')
