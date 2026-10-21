package com.yundao.bp.biz.constant;

/**
 * 结算状态（对应 {@code bp_biz_termination.settle_status}）。
 */
public enum SettleStatus {

    PENDING("待结算"),
    SETTLED("已结算"),
    WAIVED("已免除");

    private final String label;

    SettleStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
