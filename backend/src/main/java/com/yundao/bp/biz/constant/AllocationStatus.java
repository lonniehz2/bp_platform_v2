package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 配租单状态（对应 {@code bp_biz_allocation.allocation_status}）。
 *
 * <pre>
 *   PENDING_SIGN 待签约 ──签约──> SIGNED 已签约（终态）
 *        │
 *        ├──放弃/超时──> CANCELLED 已取消（终态）
 *        └──锁定超时──> EXPIRED 已过期（终态，房源自动释放）
 * </pre>
 */
public enum AllocationStatus {

    PENDING_SIGN("待签约", false),
    SIGNED("已签约", true),
    CANCELLED("已取消", true),
    EXPIRED("已过期", true);

    private final String label;
    private final boolean terminal;

    AllocationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍占用（锁定）房源。 */
    public boolean holdsHouse() {
        return this == PENDING_SIGN;
    }

    public static Set<AllocationStatus> nextOf(AllocationStatus from) {
        return switch (from) {
            case PENDING_SIGN -> Set.of(SIGNED, CANCELLED, EXPIRED);
            case SIGNED, CANCELLED, EXPIRED -> Set.of();
        };
    }
}
