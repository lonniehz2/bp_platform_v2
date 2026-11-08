package com.yundao.platform.service;

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

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select id, space_id spaceId, house_code houseCode, house_name houseName, "
                        + "asset_type_code assetTypeCode, area, inner_area innerArea, house_status houseStatus "
                        + "from bp_house where tenant_id=? and org_id=? and is_deleted=0 order by id",
                TenantContext.require(), projectId);
    }
}
