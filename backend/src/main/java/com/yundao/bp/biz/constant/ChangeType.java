package com.yundao.bp.biz.constant;

/**
 * 合同变更类型（对应 {@code bp_biz_contract_change.change_type}）。
 */
public enum ChangeType {

    RENEW("续签"),
    RENT_ADJUST("租金调整"),
    PERIOD("租期变更"),
    LESSEE("承租人变更"),
    OTHER("其他");

    private final String label;

    ChangeType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否影响租金（需同步账单/计费）。 */
    public boolean affectsRent() {
        return this == RENT_ADJUST || this == RENEW;
    }
}
