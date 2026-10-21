package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 退款单状态机（对应 {@code bp_fin_refund.refund_status}）。
 *
 * <pre>
 *   PENDING 待审批 ──批准──> APPROVED 已批准 ──打款──> SUCCESS 已退款（终态）
 *        │                      │
 *     驳回                    失败
 *        ↓                      ↓
 *   REJECTED（终态）        FAILED（可重试回 APPROVED）
 * </pre>
 */
public enum RefundStatus {

    PENDING("待审批", false),
    APPROVED("已批准", false),
    SUCCESS("已退款", true),
    FAILED("失败", false),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    RefundStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<RefundStatus> nextOf(RefundStatus from) {
        return switch (from) {
            case PENDING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(SUCCESS, FAILED);
            case FAILED -> Set.of(APPROVED);
            case SUCCESS, REJECTED -> Set.of();
        };
    }
}
