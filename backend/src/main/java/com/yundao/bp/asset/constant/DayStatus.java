package com.yundao.bp.asset.constant;

import java.util.Set;

/**
 * 日房态（对应 {@code bp_asset_house_calendar.day_status}）。
 *
 * <p>⭐ <b>短租业态的基石</b>：长租用"房源整体状态"，短租必须"按天"表达可售性，
 * 否则同一天会被重复售卖。
 *
 * <pre>
 *   AVAILABLE 可售 ──预订──> BOOKED 已预订 ──入住──> OCCUPIED 已入住
 *        │                                          │
 *        ├──停售──> CLOSED                          └──退房──> AVAILABLE
 *        └──维修──> MAINTENANCE ──修复──> AVAILABLE
 * </pre>
 */
public enum DayStatus {

    AVAILABLE("可售"),
    BOOKED("已预订"),
    OCCUPIED("已入住"),
    LEASED("已出租"),
    VACANT("空置"),
    CLOSED("停售"),
    MAINTENANCE("维修");

    private final String label;

    DayStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否可被预订/占用。 */
    public boolean bookable() {
        return this == AVAILABLE;
    }

    /** 是否由业务单据占用（预订/合同），释放时需匹配来源。 */
    public boolean occupied() {
        return this == BOOKED || this == OCCUPIED || this == LEASED;
    }

    /** 允许的迁移。 */
    public static Set<DayStatus> nextOf(DayStatus from) {
        return switch (from) {
            case AVAILABLE -> Set.of(BOOKED, OCCUPIED, LEASED, CLOSED, MAINTENANCE);
            case BOOKED -> Set.of(OCCUPIED, AVAILABLE, CLOSED);
            case OCCUPIED -> Set.of(AVAILABLE, MAINTENANCE);
            case CLOSED -> Set.of(AVAILABLE);
            case MAINTENANCE -> Set.of(AVAILABLE);
            case LEASED, VACANT -> Set.of();
        };
    }
}
