package com.yundao.bp.biz.constant;

/**
 * 换房类型（对应 {@code bp_biz_exchange.exchange_type}）。
 */
public enum ExchangeType {

    VOLUNTARY("自愿换房"),
    ADJUST("调整换房"),
    EXPEL_RELOCATE("清退安置");

    private final String label;

    ExchangeType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
