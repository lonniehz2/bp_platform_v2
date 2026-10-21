package com.yundao.bp.ops.constant;

/**
 * 告警类别（对应 {@code bp_ops_alert.alert_category}）。
 */
public enum AlertCategory {

    SAFETY("安全类"),
    DEVICE("设备类"),
    BUSINESS("业务类"),
    VIOLATION("违规类");

    private final String label;

    AlertCategory(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
