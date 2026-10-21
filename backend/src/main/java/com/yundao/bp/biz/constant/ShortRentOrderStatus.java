package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 短租订单状态（对应 {@code bp_biz_short_rent_order.order_status}）。
 *
 * <pre>
 *   PENDING 待确认 ──确认──> CONFIRMED 已确认 ──入住──> CHECKED_IN 已入住 ──退房──> CHECKED_OUT 已退房（终态）
 *        │                        │                          │
 *        └────取消───> CANCELLED 已取消（终态）                 │
 *                                 └──未到──> NO_SHOW 未到（终态）
 * </pre>
 *
 * <p>取消/退房会释放对应的日房态，让房源可再次售卖。
 */
public enum ShortRentOrderStatus {

    PENDING("待确认", false),
    CONFIRMED("已确认", false),
    CHECKED_IN("已入住", false),
    CHECKED_OUT("已退房", true),
    CANCELLED("已取消", true),
    NO_SHOW("未到", true);

    private final String label;
    private final boolean terminal;

    ShortRentOrderStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍占用房态（需在取消/退房时释放）。 */
    public boolean occupiesCalendar() {
        return this != CANCELLED && this != NO_SHOW;
    }

    public static Set<ShortRentOrderStatus> nextOf(ShortRentOrderStatus from) {
        return switch (from) {
            case PENDING -> Set.of(CONFIRMED, CANCELLED);
            case CONFIRMED -> Set.of(CHECKED_IN, CANCELLED, NO_SHOW);
            case CHECKED_IN -> Set.of(CHECKED_OUT);
            case CHECKED_OUT, CANCELLED, NO_SHOW -> Set.of();
        };
    }
}
