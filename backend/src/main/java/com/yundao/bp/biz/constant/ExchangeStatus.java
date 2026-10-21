package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 换房状态（对应 {@code bp_biz_exchange.exchange_status}）。
 *
 * <pre>
 *   APPLYING 申请中 → APPROVING 审批中 → APPROVED 已批准 → COMPLETED 已完成（终态）
 *                          └──驳回──> REJECTED（终态）
 * </pre>
 */
public enum ExchangeStatus {

    APPLYING("申请中", false),
    APPROVING("审批中", false),
    APPROVED("已批准", false),
    COMPLETED("已完成", true),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    ExchangeStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<ExchangeStatus> nextOf(ExchangeStatus from) {
        return switch (from) {
            case APPLYING -> Set.of(APPROVING, REJECTED);
            case APPROVING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(COMPLETED, REJECTED);
            case COMPLETED, REJECTED -> Set.of();
        };
    }
}
