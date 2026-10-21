package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 配租批次状态（对应 {@code bp_biz_batch.batch_status}）。
 *
 * <pre>
 *   DRAFT 草稿 → PUBLISHED 已发布 → SIGNUP 报名中 → LOTTERY 摇号中
 *     → LOTTERY_DONE 摇号完成 → SELECTING 选房中 → ALLOCATED 已配租 → CLOSED 已结束
 *   任意阶段可 CANCELLED（终态）
 * </pre>
 */
public enum BatchStatus {

    DRAFT("草稿", false),
    PUBLISHED("已发布", false),
    SIGNUP("报名中", false),
    LOTTERY("摇号中", false),
    LOTTERY_DONE("摇号完成", false),
    SELECTING("选房中", false),
    ALLOCATED("已配租", false),
    CLOSED("已结束", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    BatchStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否已过草稿阶段（可执行摇号）。 */
    public boolean canLottery() {
        return this == SIGNUP || this == PUBLISHED || this == LOTTERY;
    }

    public static Set<BatchStatus> nextOf(BatchStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PUBLISHED, CANCELLED);
            case PUBLISHED -> Set.of(SIGNUP, LOTTERY, CANCELLED);
            case SIGNUP -> Set.of(LOTTERY, CANCELLED);
            case LOTTERY -> Set.of(LOTTERY_DONE, CANCELLED);
            case LOTTERY_DONE -> Set.of(SELECTING, ALLOCATED, CANCELLED);
            case SELECTING -> Set.of(ALLOCATED, CANCELLED);
            case ALLOCATED -> Set.of(CLOSED, CANCELLED);
            case CLOSED, CANCELLED -> Set.of();
        };
    }
}
