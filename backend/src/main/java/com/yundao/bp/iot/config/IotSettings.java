package com.yundao.bp.iot.config;

import com.yundao.bp.sys.service.ConfigService;
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
        DEFAULTS.put("iot.callback.appId", "bp-test-app");
        DEFAULTS.put("iot.callback.appSecret", "bp-test-secret");
        DEFAULTS.put("iot.callback.verify", "true");
        DEFAULTS.put("iot.callback.defaultTenant", "350600");
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
        DEFAULTS.put("iot.meter.switch.arrearsThreshold", "0.01");
        DEFAULTS.put("iot.meter.switch.overdueDays", "30");
        DEFAULTS.put("iot.meter.switch.nightFrom", "22:00");
        DEFAULTS.put("iot.meter.switch.nightTo", "07:00");
        DEFAULTS.put("iot.meter.switch.dailyLimit", "3");
    }

    private final ConfigService configService;

    public IotSettings(ConfigService configService) {
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

    public java.math.BigDecimal getDecimal(String key) {
        String fallback = DEFAULTS.get(key);
        try {
            return new java.math.BigDecimal(getString(key));
        } catch (Exception e) {
            try {
                return new java.math.BigDecimal(fallback);
            } catch (Exception ignored) {
                return java.math.BigDecimal.ZERO;
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
