package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 变更审批状态（对应 {@code bp_biz_contract_change.approve_status}）。
 *
 * <pre>
 *   PENDING 待审批 ──批准──> APPROVED 已批准（生效，写回合同） ──终态
 *        └──驳回──> REJECTED 已驳回（终态）
 * </pre>
 */
public enum ApproveStatus {

    PENDING("待审批"),
    APPROVED("已批准"),
    REJECTED("已驳回");

    private final String label;

    ApproveStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == APPROVED || this == REJECTED;
    }

    public static Set<ApproveStatus> nextOf(ApproveStatus from) {
        return switch (from) {
            case PENDING -> Set.of(APPROVED, REJECTED);
            case APPROVED, REJECTED -> Set.of();
        };
    }
}
