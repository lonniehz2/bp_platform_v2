package com.yundao.bp.fin.constant;

/**
 * 流水关联的业务单据类型（对应 {@code bp_fin_cash_flow.biz_type}）。
 */
public enum FlowBizType {

    BILL("账单"),
    PAYMENT("收款"),
    REFUND("退款"),
    SUBSIDY("补贴"),
    OTHER("其他");

    private final String label;

    FlowBizType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
