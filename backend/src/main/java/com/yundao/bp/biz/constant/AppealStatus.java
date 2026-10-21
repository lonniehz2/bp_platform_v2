package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 申诉/异议状态（对应 {@code bp_biz_appeal.appeal_status}）。
 *
 * <pre>
 *   SUBMITTED 已提交 → ACCEPTED 已受理 → INVESTIGATING 调查中
 *        │                                   │
 *        │                         ┌─────────┴─────────┐
 *        │                    UPHELD 异议成立    REJECTED 异议不成立
 *        │                    （终态）            （终态）
 *        ├──撤回──> WITHDRAWN（终态）
 *        └──超期──> TIMEOUT（终态；超出 deadline_time 未提出）
 * </pre>
 */
public enum AppealStatus {

    SUBMITTED("已提交", false),
    ACCEPTED("已受理", false),
    INVESTIGATING("调查中", false),
    UPHELD("异议成立", true),
    REJECTED("异议不成立", true),
    WITHDRAWN("已撤回", true),
    TIMEOUT("超期", true);

    private final String label;
    private final boolean terminal;

    AppealStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<AppealStatus> nextOf(AppealStatus from) {
        return switch (from) {
            case SUBMITTED -> Set.of(ACCEPTED, WITHDRAWN, TIMEOUT);
            case ACCEPTED -> Set.of(INVESTIGATING, WITHDRAWN);
            case INVESTIGATING -> Set.of(UPHELD, REJECTED);
            case UPHELD, REJECTED, WITHDRAWN, TIMEOUT -> Set.of();
        };
    }
}
