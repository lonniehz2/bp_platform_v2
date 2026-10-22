package com.yundao.bp.asset.dto;

import com.yundao.bp.asset.entity.AssetHouse;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 房源视图。
 *
 * <p>⭐ 含两个<b>派生指标</b>（竞品校准采纳项 G1，不落库、只读时计算）：
 * {@code vacantDays} 空置天数、{@code lockStatusTime} 状态变更时间。
 *
 * <p>⭐ 多业态扩展：{@code spaceName}/{@code spaceType} 带出房源所属空间节点，
 * 宿舍（床位 BED）、合租等场景用于定位「这个床位属于哪个房间」。
 */
public record HouseVO(
        Long id,
        Long orgId,
        Long spaceId,
        /** 所属空间名称（房间 / 床位） */
        String spaceName,
        /** 所属空间类型：ROOM / BED 等 */
        String spaceType,
        String houseCode,
        String houseName,
        String houseType,
        String securityType,
        String unitLayout,
        Integer floorNo,
        String orientation,
        BigDecimal area,
        BigDecimal rentStandard,
        String rentUnit,
        Integer maxCapacity,
        Integer currentCapacity,
        String houseStatus,
        String houseStatusLabel,
        Long ownerOrgId,
        Long ownerPersonId,
        /** 派生的空置天数（非空置状态为 null） */
        Long vacantDays,
        LocalDateTime lockStatusTime,
        LocalDateTime createTime
) {

    public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays) {
        return from(e, statusLabel, vacantDays, null, null);
    }

    /** 带所属空间信息（宿舍/床位、合租场景用于定位）。 */
    public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays,
                               String spaceName, String spaceType) {
        if (e == null) {
            return null;
        }
        return new HouseVO(e.getId(), e.getOrgId(), e.getSpaceId(), spaceName, spaceType,
                e.getHouseCode(), e.getHouseName(), e.getHouseType(), e.getSecurityType(),
                e.getUnitLayout(), e.getFloorNo(), e.getOrientation(), e.getArea(),
                e.getRentStandard(), e.getRentUnit(), e.getMaxCapacity(),
                e.getCurrentCapacity(), e.getHouseStatus(), statusLabel,
                e.getOwnerOrgId(), e.getOwnerPersonId(), vacantDays,
                e.getLockStatusTime(), e.getCreateTime());
    }
}
