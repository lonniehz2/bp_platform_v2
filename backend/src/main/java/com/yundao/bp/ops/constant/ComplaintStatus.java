package com.yundao.bp.ops.constant;

import java.util.Set;

/**
 * 投诉/建议处理状态（对应 {@code bp_ops_complaint.handle_status}）。
 *
 * <pre>
 *   PENDING 待处理 → HANDLING 处理中 → HANDLED 已处理 → CLOSED 已归档
 * </pre>
 */
public enum ComplaintStatus {

    PENDING("待处理"),
    HANDLING("处理中"),
    HANDLED("已处理"),
    CLOSED("已归档");

    private final String label;

    ComplaintStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == CLOSED;
    }

    public static Set<ComplaintStatus> nextOf(ComplaintStatus from) {
        return switch (from) {
            case PENDING -> Set.of(HANDLING, HANDLED);
            case HANDLING -> Set.of(HANDLED);
            case HANDLED -> Set.of(CLOSED);
            case CLOSED -> Set.of();
        };
    }
}
