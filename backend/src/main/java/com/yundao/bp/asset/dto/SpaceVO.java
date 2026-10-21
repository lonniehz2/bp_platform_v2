package com.yundao.bp.asset.dto;

import com.yundao.bp.asset.entity.AssetSpace;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

/**
 * 空间节点视图（含子节点，用于树形返回）。
 */
public record SpaceVO(
        Long id,
        Long orgId,
        Long parentId,
        String spaceCode,
        String spaceName,
        String spaceType,
        String spacePath,
        String pathCode,
        Integer spaceLevel,
        String fullName,
        BigDecimal area,
        Integer sortNo,
        String locationCode,
        String status,
        List<SpaceVO> children
) {
    public static SpaceVO from(AssetSpace e) {
        if (e == null) {
            return null;
        }
        return new SpaceVO(e.getId(), e.getOrgId(), e.getParentId(), e.getSpaceCode(),
                e.getSpaceName(), e.getSpaceType(), e.getSpacePath(), e.getPathCode(),
                e.getSpaceLevel(), e.getFullName(), e.getArea(), e.getSortNo(),
                e.getLocationCode(), e.getStatus(), new ArrayList<>());
    }
}
