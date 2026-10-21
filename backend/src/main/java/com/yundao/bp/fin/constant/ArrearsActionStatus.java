package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 欠费处置单状态（对应 {@code bp_fin_arrears_action.action_status}）。
 *
 * <pre>
 *   PENDING 待执行 ──执行──> EXECUTED 已执行 ──缴清/撤销──> REVOKED 已撤销
 *        │                        │
 *        └──撤销──> REVOKED        └──执行失败──> FAILED（可重试回 PENDING）
 * </pre>
 */
public enum ArrearsActionStatus {

    PENDING("待执行"),
    EXECUTED("已执行"),
    REVOKED("已撤销"),
    FAILED("执行失败");

    private final String label;

    ArrearsActionStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == REVOKED;
    }

    public static Set<ArrearsActionStatus> nextOf(ArrearsActionStatus from) {
        return switch (from) {
            case PENDING -> Set.of(EXECUTED, REVOKED, FAILED);
            case EXECUTED -> Set.of(REVOKED);
            case FAILED -> Set.of(PENDING, REVOKED);
            case REVOKED -> Set.of();
        };
    }
}
