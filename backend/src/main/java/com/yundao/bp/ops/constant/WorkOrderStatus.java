package com.yundao.bp.ops.constant;

import java.util.Map;
import java.util.Set;

/**
 * 工单状态机（对应 {@code bp_ops_workorder.order_status}）。
 *
 * <pre>
 *   PENDING ──派单──> ASSIGNED ──接单──> ACCEPTED ──开始──> PROCESSING ──完工──> FINISHED ──闭环──> CLOSED
 *      │                 │                 │                    │
 *      └─────────────────┴─────────────────┴────────────────────┴──> CANCELLED（取消，终态）
 *                        └──驳回──> REJECTED（终态）
 * </pre>
 *
 * <p>业务约束：
 * <ul>
 *   <li>{@code CLOSED} 是唯一"闭环"终态，闭环时间是考核指标</li>
 *   <li>{@code FINISHED} 之后才能 {@code CLOSED}（先完工再确认）</li>
 *   <li>{@code REJECTED} / {@code CANCELLED} 为异常终态，不计入 SLA 达标</li>
 * </ul>
 */
public enum WorkOrderStatus {

    PENDING("待派单", false),
    ASSIGNED("已派单", false),
    ACCEPTED("已接单", false),
    PROCESSING("处理中", false),
    FINISHED("已完工", false),
    CLOSED("已闭环", true),
    CANCELLED("已取消", true),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    WorkOrderStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    /** 是否终态（不可再流转）。 */
    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍在处理中（未终态）。 */
    public boolean isOpen() {
        return !terminal;
    }

    /** 允许的迁移。 */
    public static Set<WorkOrderStatus> nextOf(WorkOrderStatus from) {
        return switch (from) {
            case PENDING -> Set.of(ASSIGNED, CANCELLED);
            case ASSIGNED -> Set.of(ACCEPTED, REJECTED, CANCELLED);
            case ACCEPTED -> Set.of(PROCESSING, FINISHED, CANCELLED);
            case PROCESSING -> Set.of(FINISHED, CANCELLED);
            case FINISHED -> Set.of(CLOSED);
            case CLOSED, CANCELLED, REJECTED -> Set.of();
        };
    }

    /** 已派单/已接单/处理中 —— 用于"我的待办"统计。 */
    public static Set<WorkOrderStatus> IN_PROGRESS = Set.of(ASSIGNED, ACCEPTED, PROCESSING);

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, WorkOrderStatus::label));
    }
}
