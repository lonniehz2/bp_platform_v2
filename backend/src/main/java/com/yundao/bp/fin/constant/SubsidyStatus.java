package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 补贴发放状态（对应 {@code bp_fin_subsidy_record.record_status}）。
 *
 * <pre>
 *   PENDING 待发放 ──发起──> PAYING 发放中 ──成功──> SUCCESS 已发放（终态）
 *        │                       │
 *        │                    失败/退回
 *        │                       ↓
 *        │                  FAILED 发放失败（可重试回 PAYING）
 *        └──────────────────> RETURNED 已退回（终态）
 * </pre>
 */
public enum SubsidyStatus {

    PENDING("待发放"),
    PAYING("发放中"),
    SUCCESS("已发放"),
    FAILED("发放失败"),
    RETURNED("已退回");

    private final String label;

    SubsidyStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == SUCCESS || this == RETURNED;
    }

    public static Set<SubsidyStatus> nextOf(SubsidyStatus from) {
        return switch (from) {
            case PENDING -> Set.of(PAYING, RETURNED);
            case PAYING -> Set.of(SUCCESS, FAILED, RETURNED);
            case FAILED -> Set.of(PAYING, RETURNED);
            case SUCCESS, RETURNED -> Set.of();
        };
    }
}
