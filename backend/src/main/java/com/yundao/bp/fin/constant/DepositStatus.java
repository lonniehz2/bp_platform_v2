package com.yundao.bp.fin.constant;

/**
 * 押金台账状态（对应 {@code bp_fin_deposit.deposit_status}）。
 */
public enum DepositStatus {

    HELD("已收取"),
    PARTIAL_REFUND("部分退还"),
    REFUNDED("已退还"),
    DEDUCTED("已抵扣");

    private final String label;

    DepositStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isClosed() {
        return this == REFUNDED || this == DEDUCTED;
    }
}
