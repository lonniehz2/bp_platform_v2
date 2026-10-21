package com.yundao.bp.fin.constant;

/**
 * 资金流水类型（对应 {@code bp_fin_cash_flow.flow_type}）。
 *
 * <p>金额带符号：收入为正、支出为负，便于直接求和得到净额。
 */
public enum FlowType {

    INCOME("收入"),
    EXPENSE("支出"),
    TRANSFER("转账"),
    ADJUST("调整");

    private final String label;

    FlowType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 该类型金额应为正还是负。 */
    public boolean positive() {
        return this == INCOME;
    }
}
