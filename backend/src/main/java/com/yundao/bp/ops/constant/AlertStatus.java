package com.yundao.bp.ops.constant;

import java.util.Map;
import java.util.Set;

/**
 * 告警状态机（对应 {@code bp_ops_alert.alert_status}）。
 *
 * <pre>
 *   PENDING ──处置──> HANDLING ──办结──> HANDLED（闭环）
 *      │                 │
 *      ├──误报───────────┴──> IGNORED（终态）
 *      └──超时/重大──> ESCALATED（已升级，仍可继续处置）
 * </pre>
 */
public enum AlertStatus {

    PENDING("待处理", false),
    HANDLING("处理中", false),
    HANDLED("已闭环", true),
    IGNORED("误报忽略", true),
    ESCALATED("已升级", false);

    private final String label;
    private final boolean terminal;

    AlertStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍未闭环（用于"待处理告警数"统计）。 */
    public boolean isOpen() {
        return !terminal;
    }

    public static Set<AlertStatus> nextOf(AlertStatus from) {
        return switch (from) {
            case PENDING -> Set.of(HANDLING, IGNORED, ESCALATED);
            case ESCALATED -> Set.of(HANDLING, IGNORED);
            case HANDLING -> Set.of(HANDLED, IGNORED, ESCALATED);
            case HANDLED, IGNORED -> Set.of();
        };
    }

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, AlertStatus::label));
    }
}
