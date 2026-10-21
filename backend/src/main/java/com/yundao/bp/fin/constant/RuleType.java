package com.yundao.bp.fin.constant;

/**
 * 计费规则类型（对应 {@code bp_fin_billing_rule.rule_type}）。
 *
 * <p>多条规则命中时按 {@code priority} 取高者。
 */
public enum RuleType {

    STANDARD("标准价"),
    TIERED("阶梯"),
    DISCOUNT("折扣"),
    EXEMPT("减免");

    private final String label;

    RuleType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
