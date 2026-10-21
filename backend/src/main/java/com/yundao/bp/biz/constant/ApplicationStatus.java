package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 申请单状态机（对应 {@code bp_biz_application.application_status}）。
 *
 * <pre>
 *   DRAFT 草稿 ──提交──> SUBMITTED 已提交 ──受理──> ACCEPTED 已受理
 *                                                      │
 *                                                      ↓
 *                              REVIEWING 审核中 ←──┬──┤
 *                                   │            │  │
 *                          需补件 ──┘            │  └──不通过──> REJECTED（终态）
 *                                   ↓            │
 *                            SUPPLEMENT 待补件 ─┘
 *                                   │
 *                          审核通过 ─┴──> APPROVED 已通过（终态，可进入配租）
 * </pre>
 *
 * <p>另有 {@code CANCELLED} 已取消（终态，申请人主动撤回）。
 */
public enum ApplicationStatus {

    DRAFT("草稿", false),
    SUBMITTED("已提交", false),
    ACCEPTED("已受理", false),
    REVIEWING("审核中", false),
    SUPPLEMENT("待补件", false),
    APPROVED("已通过", true),
    REJECTED("不通过", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    ApplicationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍在流程中（可做审核动作）。 */
    public boolean isInReview() {
        return this == ACCEPTED || this == REVIEWING || this == SUPPLEMENT;
    }

    public static Set<ApplicationStatus> nextOf(ApplicationStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(SUBMITTED, CANCELLED);
            case SUBMITTED -> Set.of(ACCEPTED, CANCELLED);
            case ACCEPTED -> Set.of(REVIEWING, REJECTED, CANCELLED);
            case REVIEWING -> Set.of(APPROVED, REJECTED, SUPPLEMENT);
            case SUPPLEMENT -> Set.of(REVIEWING, CANCELLED);
            case APPROVED, REJECTED, CANCELLED -> Set.of();
        };
    }
}
