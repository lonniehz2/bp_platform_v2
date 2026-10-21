package com.yundao.bp.ops.constant;

/**
 * SLA 达标状态（对应 {@code bp_ops_workorder.sla_status}）。
 */
public enum SlaStatus {

    ON_TIME("按时"),
    RESPONSE_TIMEOUT("响应超时"),
    FINISH_TIMEOUT("完工超时");

    private final String label;

    SlaStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
