package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 信用记录状态（对应 {@code bp_biz_credit_record.status}）。
 *
 * <pre>
 *   EFFECTIVE 生效中 ──期满──> EXPIRED 已解除（终态）
 *        └──复议/纠错撤销──> REVOKED 已撤销（终态）
 * </pre>
 */
public enum CreditStatus {

    EFFECTIVE("生效中"),
    EXPIRED("已解除"),
    REVOKED("已撤销");

    private final String label;

    CreditStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this != EFFECTIVE;
    }

    public static Set<CreditStatus> nextOf(CreditStatus from) {
        return switch (from) {
            case EFFECTIVE -> Set.of(EXPIRED, REVOKED);
            case EXPIRED, REVOKED -> Set.of();
        };
    }
}
