package com.yundao.bp.dev.constant;

/**
 * 设备事件类型。
 *
 * <p>告警类（LOW_BATTERY / TAMPER / TRIAL_ERROR / DURESS / POWER_OVER）会进入告警视图，
 * 其余为记录类事件。
 */
public enum DevEventType {

    OPEN("开锁", "INFO", false),
    ONLINE("上线", "INFO", false),
    OFFLINE("离线", "WARN", true),
    LOW_BATTERY("低电量告警", "WARN", true),
    BATTERY_RESTORED("低电解除", "INFO", false),
    TAMPER("防拆告警", "CRITICAL", true),
    TRIAL_ERROR("试错告警（密码连续错误）", "WARN", true),
    DURESS("胁迫告警", "CRITICAL", true),
    POWER_OVER("超功率告警", "WARN", true),
    LOCAL_SWITCH("本地合闸", "INFO", false),
    METER_READ("抄表读数", "INFO", false),
    OTHER("其他", "INFO", false);

    private final String label;
    private final String defaultLevel;
    private final boolean alarm;

    DevEventType(String label, String defaultLevel, boolean alarm) {
        this.label = label;
        this.defaultLevel = defaultLevel;
        this.alarm = alarm;
    }

    public String label() { return label; }
    public String defaultLevel() { return defaultLevel; }
    public boolean alarm() { return alarm; }

    public static DevEventType of(String code) {
        if (code == null) {
            return OTHER;
        }
        for (DevEventType t : values()) {
            if (t.name().equalsIgnoreCase(code)) {
                return t;
            }
        }
        return OTHER;
    }
}
