package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 账单状态（对应 {@code bp_fin_bill.bill_status}）。
 *
 * <pre>
 *   UNPAID 未缴 ──部分收款──> PARTIAL 部分缴 ──收满──> PAID 已缴
 *      │                        │
 *      └──过缴费截止日──> OVERDUE 已逾期（仍可收）
 *   UNPAID/PARTIAL/OVERDUE ──减免──> WAIVED 已免除
 *   任意未缴 ──作废──> CANCELLED（终态）
 * </pre>
 */
public enum BillStatus {

    UNPAID("未缴", false),
    PARTIAL("部分缴", false),
    PAID("已缴", true),
    OVERDUE("已逾期", false),
    WAIVED("已免除", true),
    CANCELLED("已作废", true);

    private final String label;
    private final boolean terminal;

    BillStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否还欠钱（可收款）。 */
    public boolean isOutstanding() {
        return this == UNPAID || this == PARTIAL || this == OVERDUE;
    }

    public static Set<BillStatus> nextOf(BillStatus from) {
        return switch (from) {
            case UNPAID -> Set.of(PARTIAL, PAID, OVERDUE, WAIVED, CANCELLED);
            case PARTIAL -> Set.of(PARTIAL, PAID, OVERDUE, WAIVED, CANCELLED);
            case OVERDUE -> Set.of(PARTIAL, PAID, WAIVED, CANCELLED);
            case PAID, WAIVED, CANCELLED -> Set.of();
        };
    }
}
