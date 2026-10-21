package com.yundao.bp.asset.dto;

import com.yundao.bp.asset.entity.AssetHouse;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 房源视图。
 *
 * <p>⭐ 含两个<b>派生指标</b>（竞品校准采纳项 G1，不落库、只读时计算）：
 * {@code vacantDays} 空置天数、{@code lockStatusTime} 状态变更时间。
 */
public record HouseVO(
        Long id,
        Long orgId,
        Long spaceId,
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
        if (e == null) {
            return null;
        }
        return new HouseVO(e.getId(), e.getOrgId(), e.getSpaceId(), e.getHouseCode(),
                e.getHouseName(), e.getHouseType(), e.getSecurityType(), e.getUnitLayout(),
                e.getFloorNo(), e.getOrientation(), e.getArea(), e.getRentStandard(),
                e.getRentUnit(), e.getMaxCapacity(), e.getCurrentCapacity(),
                e.getHouseStatus(), statusLabel, e.getOwnerOrgId(), e.getOwnerPersonId(),
                vacantDays, e.getLockStatusTime(), e.getCreateTime());
    }
}
