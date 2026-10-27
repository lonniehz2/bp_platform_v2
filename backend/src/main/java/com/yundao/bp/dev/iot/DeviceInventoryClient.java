package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 设备台账拉取（平台 → IoT）。配置 {@code bp.dev.device-mode=mock|real}。
 *
 * <p>用于增量同步：按更新时间拉取设备，写入 {@code bp_dev_device}。
 */
public interface DeviceInventoryClient {

    List<DeviceInfo> fetch(LocalDateTime since);

    record DeviceInfo(String deviceId, String deviceMac, String deviceName, String deviceType,
                      String deviceModel, String firmware, Integer onlineStatus,
                      Integer battery, String rssi, LocalDateTime lastReportTime,
                      String installAddress) {
    }
}
