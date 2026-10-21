package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 退租单状态机（对应 {@code bp_biz_termination.termination_status}）。
 *
 * <pre>
 *   APPLYING 申请中 ──提交审批──> APPROVING 审批中 ──批准──> APPROVED 已批准
 *                                      │                      │
 *                                   驳回                    办结（验房+结算+释放房源+回收授权）
 *                                      ↓                      ↓
 *                                REJECTED（终态）        COMPLETED（终态）
 *   APPLYING ──撤单──> CANCELLED（终态）
 * </pre>
 *
 * <p><b>COMPLETED 的四个前置</b>（缺一不可）：
 * 验房完成、结算完成、房源已释放、授权已回收。
 */
public enum TerminationStatus {

    APPLYING("申请中", false),
    APPROVING("审批中", false),
    APPROVED("已批准", false),
    REJECTED("已驳回", true),
    COMPLETED("已完成", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    TerminationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<TerminationStatus> nextOf(TerminationStatus from) {
        return switch (from) {
            case APPLYING -> Set.of(APPROVING, CANCELLED);
            case APPROVING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(COMPLETED);
            case REJECTED, COMPLETED, CANCELLED -> Set.of();
        };
    }
}
