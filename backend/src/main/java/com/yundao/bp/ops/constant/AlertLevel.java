package com.yundao.bp.ops.constant;

/**
 * 告警级别（对应 {@code bp_ops_alert.alert_level}）。
 *
 * <p>级别决定 SLA 与是否推送短信/大屏红色告警：
 * {@code URGENT} 立即处置，{@code IMPORTANT} 当日处置，{@code NORMAL} 按常规流转。
 */
public enum AlertLevel {

    URGENT("紧急", 1),
    IMPORTANT("重要", 2),
    NORMAL("一般", 3);

    private final String label;
    private final int weight;

    AlertLevel(String label, int weight) {
        this.label = label;
        this.weight = weight;
    }

    public String label() {
        return label;
    }

    /** 权重（1 最高），用于排序。 */
    public int weight() {
        return weight;
    }
}
