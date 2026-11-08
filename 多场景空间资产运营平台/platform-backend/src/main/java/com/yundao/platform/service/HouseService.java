package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class HouseService {

    private final JdbcTemplate jdbc;

    public HouseService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> update(long houseId, HouseUpdate cmd) {
        if (cmd.houseStatus() != null && !List.of("VACANT", "ALLOCATED", "OCCUPIED", "FROZEN").contains(cmd.houseStatus())) {
            throw BizException.param("房态不合法");
        }
        int updated = jdbc.update("update bp_house set area=coalesce(?,area), inner_area=coalesce(?,inner_area), "
                        + "house_status=coalesce(?,house_status), asset_type_code=coalesce(?,asset_type_code), "
                        + "layout_type=coalesce(?,layout_type), orientation=coalesce(?,orientation), "
                        + "floor_no=coalesce(?,floor_no), total_floors=coalesce(?,total_floors), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.area(), cmd.innerArea(), cmd.houseStatus(), cmd.assetTypeCode(),
                cmd.layoutType(), cmd.orientation(), cmd.floorNo(), cmd.totalFloors(),
                houseId, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("房源不存在");
        }
        return Map.of("id", houseId, "houseStatus", cmd.houseStatus() == null ? "UNCHANGED" : cmd.houseStatus());
    }

    public record HouseUpdate(java.math.BigDecimal area, java.math.BigDecimal innerArea,
                              String houseStatus, String assetTypeCode, String layoutType,
                              String orientation, Integer floorNo, Integer totalFloors) {
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select id, space_id spaceId, house_code houseCode, house_name houseName, "
                        + "asset_type_code assetTypeCode, area, inner_area innerArea, house_status houseStatus, "
                        + "layout_type layoutType, orientation, floor_no floorNo, total_floors totalFloors "
                        + "from bp_house where tenant_id=? and org_id=? and is_deleted=0 order by id",
                TenantContext.require(), projectId);
    }
}
