package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 年审（复核）状态（对应 {@code bp_biz_annual_review.review_status}）。
 *
 * <pre>
 *   PENDING 待复核 → REVIEWING 复核中 → DONE 已完成（终态）
 *   超期未复核 → OVERDUE 已逾期（可继续复核 → DONE）
 * </pre>
 */
public enum ReviewStatus {

    PENDING("待复核", false),
    REVIEWING("复核中", false),
    DONE("已完成", true),
    OVERDUE("已逾期", false);

    private final String label;
    private final boolean terminal;

    ReviewStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<ReviewStatus> nextOf(ReviewStatus from) {
        return switch (from) {
            case PENDING -> Set.of(REVIEWING, OVERDUE);
            case REVIEWING -> Set.of(DONE, OVERDUE);
            case OVERDUE -> Set.of(REVIEWING, DONE);
            case DONE -> Set.of();
        };
    }
}
