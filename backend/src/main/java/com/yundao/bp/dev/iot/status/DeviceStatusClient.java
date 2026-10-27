package com.yundao.bp.dev.iot.status;

import java.util.List;

/**
 * 批量设备状态查询（平台 → IoT）。
 *
 * <p>配置 {@code bp.iot.status-mode=mock|real}；契约见 21_IoT侧需求规格说明书 §2。
 */
public interface DeviceStatusClient {

    List<DeviceStatus> batch(List<String> lockIds);

    record DeviceStatus(String lockId, boolean online, Integer battery, Integer rssi,
                        String lastReportTime, String firmware) {
    }
}
