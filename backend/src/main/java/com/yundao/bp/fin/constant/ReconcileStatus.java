package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 对账状态（对应 {@code bp_fin_reconcile.reconcile_status}）。
 *
 * <pre>
 *   MATCHED 一致（终态）
 *   DIFF 有差异 ──人工处理──> HANDLED 已处理（终态）
 * </pre>
 */
public enum ReconcileStatus {

    MATCHED("一致"),
    DIFF("有差异"),
    HANDLED("已处理");

    private final String label;

    ReconcileStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == MATCHED || this == HANDLED;
    }

    public static Set<ReconcileStatus> nextOf(ReconcileStatus from) {
        return switch (from) {
            case DIFF -> Set.of(HANDLED, MATCHED);
            case MATCHED, HANDLED -> Set.of();
        };
    }
}
