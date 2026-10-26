# -*- coding: utf-8 -*-
"""IoT 对接契约参数：写入系统参数（分组 IOT）+ 后端读取服务。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# 9 条契约 + 3 个配套项
ITEMS = [
    ('iot.callback.signAlgorithm', 'v2-hmac-sha256', 'STRING',
     '回调签名算法：v2-hmac-sha256 或 legacy-md5-aes'),
    ('iot.callback.timestampToleranceSeconds', '300', 'INT',
     '回调时间戳容忍窗口（秒），超出视为重放'),
    ('iot.callback.nonceCacheMinutes', '10', 'INT',
     '回调 Nonce 缓存时长（分钟），用于防重放'),
    ('iot.callback.batchLimit', '200', 'INT',
     '回调/批量接口单次最大条数'),
    ('iot.callback.qps', '50', 'INT',
     '回调接口限流（次/秒），0 表示不限'),
    ('iot.command.timeoutSeconds', '10', 'INT',
     '设备指令超时（秒），超时转 TIMEOUT 并重试'),
    ('iot.command.maxRetry', '3', 'INT',
     '设备指令最大重试次数'),
    ('iot.grantTask.timeoutSeconds', '180', 'INT',
     '授权任务超时（秒），超时置 TIMEOUT 并重试'),
    ('iot.heartbeat.intervalSeconds', '60', 'INT',
     '设备心跳间隔（秒），IoT 上报频率参考值'),
    ('iot.offline.thresholdSeconds', '180', 'INT',
     '离线判定阈值（秒）：超过该时长无心跳即判离线'),
    ('iot.meter.reportPeriod', 'ELEC:DAILY,WATER:DAILY', 'STRING',
     '表计上报周期：电表/水表均为每日（如 ELEC:DAILY,WATER:DAILY,GAS:DAILY）'),
    ('iot.meter.switch.delayMinutes', '10', 'INT',
     '电表拉闸延迟执行（分钟），期间可撤销'),
]

# ---------- 后端读取服务 ----------
SERVICE = '''package com.yundao.bp.iot.config;

import com.yundao.bp.sys.service.SysConfigService;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * IoT 对接契约参数（可在「系统支撑 → 系统参数」分组 IOT 中调整）。
 *
 * <p>所有参数都有代码内默认值：配置缺失或格式非法时回落到默认值，避免联调时因漏配启动失败。
 */
@Component
public class IotSettings {

    public static final String GROUP = "IOT";

    /** 键 → 默认值（顺序即页面展示顺序）。 */
    private static final Map<String, String> DEFAULTS = new LinkedHashMap<>();

    static {
        DEFAULTS.put("iot.callback.signAlgorithm", "v2-hmac-sha256");
        DEFAULTS.put("iot.callback.timestampToleranceSeconds", "300");
        DEFAULTS.put("iot.callback.nonceCacheMinutes", "10");
        DEFAULTS.put("iot.callback.batchLimit", "200");
        DEFAULTS.put("iot.callback.qps", "50");
        DEFAULTS.put("iot.command.timeoutSeconds", "10");
        DEFAULTS.put("iot.command.maxRetry", "3");
        DEFAULTS.put("iot.grantTask.timeoutSeconds", "180");
        DEFAULTS.put("iot.heartbeat.intervalSeconds", "60");
        DEFAULTS.put("iot.offline.thresholdSeconds", "180");
        DEFAULTS.put("iot.meter.reportPeriod", "ELEC:DAILY,WATER:DAILY");
        DEFAULTS.put("iot.meter.switch.delayMinutes", "10");
    }

    private final SysConfigService configService;

    public IotSettings(SysConfigService configService) {
        this.configService = configService;
    }

    public static Map<String, String> defaults() {
        return new LinkedHashMap<>(DEFAULTS);
    }

    public String getString(String key) {
        String fallback = DEFAULTS.get(key);
        try {
            String v = configService.getString(key, fallback);
            return (v == null || v.isBlank()) ? fallback : v.trim();
        } catch (Exception e) {
            return fallback;
        }
    }

    public int getInt(String key) {
        String fallback = DEFAULTS.get(key);
        String v = getString(key);
        try {
            return Integer.parseInt(v);
        } catch (Exception e) {
            try {
                return Integer.parseInt(fallback);
            } catch (Exception ignored) {
                return 0;
            }
        }
    }

    // ---------- 语义化快捷方法（后续回调/指令模块直接用） ----------

    public String signAlgorithm() {
        return getString("iot.callback.signAlgorithm");
    }

    public int timestampToleranceSeconds() {
        return getInt("iot.callback.timestampToleranceSeconds");
    }

    public int nonceCacheMinutes() {
        return getInt("iot.callback.nonceCacheMinutes");
    }

    public int callbackBatchLimit() {
        return getInt("iot.callback.batchLimit");
    }

    public int callbackQps() {
        return getInt("iot.callback.qps");
    }

    public int commandTimeoutSeconds() {
        return getInt("iot.command.timeoutSeconds");
    }

    public int commandMaxRetry() {
        return getInt("iot.command.maxRetry");
    }

    public int grantTaskTimeoutSeconds() {
        return getInt("iot.grantTask.timeoutSeconds");
    }

    public int heartbeatIntervalSeconds() {
        return getInt("iot.heartbeat.intervalSeconds");
    }

    public int offlineThresholdSeconds() {
        return getInt("iot.offline.thresholdSeconds");
    }

    public String meterReportPeriod() {
        return getString("iot.meter.reportPeriod");
    }

    public int meterSwitchDelayMinutes() {
        return getInt("iot.meter.switch.delayMinutes");
    }
}
'''

path = os.path.join(BK, 'iot', 'config', 'IotSettings.java')
os.makedirs(os.path.dirname(path), exist_ok=True)
if not os.path.exists(path):
    io.open(path, 'w', encoding='utf-8', newline='').write(SERVICE)
    print('已创建 IotSettings.java')

print('参数条目:', len(ITEMS))
