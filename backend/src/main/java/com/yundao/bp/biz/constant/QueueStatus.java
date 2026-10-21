package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 轮候状态（对应 {@code bp_biz_waiting_queue.queue_status}）。
 *
 * <pre>
 *   WAITING 轮候中 ──中签──> WON 已中签 ──配租成功──> ALLOCATED 已配租（终态）
 *        │                    │
 *        ├──冻结──> FROZEN ────┘（解冻回 WAITING）
 *        ├──退出──> EXITED（终态）
 *        └──资格过期──> EXPIRED（终态）
 * </pre>
 */
public enum QueueStatus {

    WAITING("轮候中", false),
    WON("已中签", false),
    ALLOCATED("已配租", true),
    FROZEN("已冻结", false),
    EXITED("已退出", true),
    EXPIRED("已过期", true);

    private final String label;
    private final boolean terminal;

    QueueStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否还能被摇号/配租选中。 */
    public boolean selectable() {
        return this == WAITING;
    }

    public static Set<QueueStatus> nextOf(QueueStatus from) {
        return switch (from) {
            case WAITING -> Set.of(WON, FROZEN, EXITED, EXPIRED);
            case FROZEN -> Set.of(WAITING, EXITED);
            case WON -> Set.of(ALLOCATED, WAITING, EXITED);
            case ALLOCATED, EXITED, EXPIRED -> Set.of();
        };
    }
}
