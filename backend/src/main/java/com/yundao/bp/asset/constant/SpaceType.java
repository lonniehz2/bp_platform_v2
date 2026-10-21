package com.yundao.bp.asset.constant;

import java.util.List;

/**
 * 空间类型与层级规则。
 *
 * <p>设计依据：{@code 03_数据库设计说明.md} §3.2.0（已确认层级）。
 *
 * <pre>
 * 小区（bp_iam_org 承载，org_type=COMMUNITY）
 *   └ 楼栋 BUILDING
 *       └ 单元 UNIT
 *           └ 楼层 FLOOR
 *               └ 房间 ROOM
 *                   └ 床位 BED   （宿舍/合租场景的内部房间）
 * </pre>
 *
 * <p>不属于主层级链的：{@code PARKING / GARAGE / SITE}。
 */
public enum SpaceType {

    AREA(1, "片区"),
    BUILDING(2, "楼栋"),
    UNIT(3, "单元"),
    FLOOR(4, "楼层"),
    ROOM(5, "房间"),
    BED(6, "床位"),
    PARKING(1, "车位"),
    GARAGE(1, "车库"),
    SITE(1, "场地");

    private final int defaultLevel;
    private final String label;

    SpaceType(int defaultLevel, String label) {
        this.defaultLevel = defaultLevel;
        this.label = label;
    }

    public int defaultLevel() {
        return defaultLevel;
    }

    public String label() {
        return label;
    }

    /** 主层级链（楼栋以下），用于校验父子关系。 */
    public static final List<SpaceType> MAIN_CHAIN =
            List.of(BUILDING, UNIT, FLOOR, ROOM, BED);

    /** 允许哪些子类型。返回 null 表示只允许主链下一级。 */
    public static SpaceType nextOf(SpaceType parent) {
        switch (parent) {
            case BUILDING: return UNIT;
            case UNIT:     return FLOOR;
            case FLOOR:    return ROOM;
            case ROOM:     return BED;
            default:       return null;   // 顶级（无父）或 BED/车位等为叶子
        }
    }

    public boolean isLeaf() {
        return this == BED || this == PARKING || this == GARAGE || this == SITE;
    }

    /** 是否允许作为房源挂载点（房源挂 ROOM；床位出租时挂 BED）。 */
    public boolean canHostHouse() {
        return this == ROOM || this == BED;
    }
}
