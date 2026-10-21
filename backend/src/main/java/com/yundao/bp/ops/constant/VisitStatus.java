package com.yundao.bp.ops.constant;

import java.util.Set;

/**
 * 走访状态（对应 {@code bp_ops_house_visit.visit_status}）。
 *
 * <pre>
 *   PENDING 待走访 ──完成──> DONE 已完成
 *      ├──拒访──> REFUSED
 *      ├──无人──> ABSENT
 *      └──取消──> CANCELLED
 * </pre>
 */
public enum VisitStatus {

    PENDING("待走访"),
    DONE("已完成"),
    REFUSED("拒访"),
    ABSENT("无人"),
    CANCELLED("已取消");

    private final String label;

    VisitStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this != PENDING;
    }

    public static Set<VisitStatus> nextOf(VisitStatus from) {
        return from == PENDING
                ? Set.of(DONE, REFUSED, ABSENT, CANCELLED)
                : Set.of();
    }
}
