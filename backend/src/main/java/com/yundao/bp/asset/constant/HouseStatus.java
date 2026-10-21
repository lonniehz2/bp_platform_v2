package com.yundao.bp.asset.constant;

import java.util.Set;

/**
 * 房源状态机。
 *
 * <p>权威状态在 {@code bp_asset_house.house_status}；
 * 批次内的 {@code bp_biz_batch_house.in_pool_status} 只是它的视图，必须同事务更新。
 */
public enum HouseStatus {

    PENDING_ALLOC("待分配"),
    LOCKED("锁定中"),
    ALLOCATED("已配租"),
    OCCUPIED("已入住"),
    VACANT("空置待配"),
    MAINTENANCE("维修中"),
    DISABLED("停用");

    private final String label;

    HouseStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 可参与配租的房源池状态。 */
    public static final Set<HouseStatus> POOLABLE = Set.of(PENDING_ALLOC, VACANT);

    /** 允许的状态迁移。 */
    public static Set<HouseStatus> nextOf(HouseStatus from) {
        return switch (from) {
            case PENDING_ALLOC -> Set.of(LOCKED, VACANT, MAINTENANCE, DISABLED);
            case LOCKED        -> Set.of(ALLOCATED, PENDING_ALLOC, VACANT);
            case ALLOCATED     -> Set.of(OCCUPIED, VACANT, MAINTENANCE);
            case OCCUPIED      -> Set.of(VACANT, MAINTENANCE, ALLOCATED);
            case VACANT        -> Set.of(LOCKED, PENDING_ALLOC, MAINTENANCE, DISABLED);
            case MAINTENANCE   -> Set.of(VACANT, PENDING_ALLOC, DISABLED);
            case DISABLED      -> Set.of(VACANT, PENDING_ALLOC);
        };
    }

    public boolean canTransitTo(HouseStatus target) {
        return target != null && nextOf(this).contains(target);
    }
}
