package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业房屋与业主关系。房屋复用 bp_asset_house。 */
@Service
public class PropertyUnitService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyUnitService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> buildings(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, space_name buildingName, space_code buildingCode from bp_asset_space "
                        + "where tenant_id=? and org_id=? and space_type='BUILDING' and is_deleted=0 "
                        + "order by sort_no, space_name",
                TenantContext.tenantId(), projectId);
    }

    public List<Map<String, Object>> units(Long projectId, Long buildingId) {
        requireProject(projectId);
        String where = " where h.tenant_id=? and h.org_id=? and h.is_deleted=0 and s.space_type='ROOM' ";
        Object[] args;
        if (buildingId == null) {
            args = new Object[]{TenantContext.tenantId(), projectId};
        } else {
            where += " and s.space_path like concat(?, '%') ";
            args = new Object[]{TenantContext.tenantId(), projectId, buildingId + "/"};
        }
        return jdbc.queryForList(
                "select h.id, h.house_code houseCode, h.house_name houseName, h.space_id spaceId, "
                        + "s.space_name spaceName, s.space_type spaceType, h.area, h.house_status houseStatus, "
                        + "(select p.person_name from prop_owner_unit ou join bp_person p on p.id=ou.person_id "
                        + " where ou.house_id=h.id and ou.is_primary=1 and ou.status='ACTIVE' "
                        + " and ou.is_deleted=0 limit 1) ownerName, "
                        + "(select p.phone from prop_owner_unit ou join bp_person p on p.id=ou.person_id "
                        + " where ou.house_id=h.id and ou.is_primary=1 and ou.status='ACTIVE' "
                        + " and ou.is_deleted=0 limit 1) ownerPhone "
                        + "from bp_asset_house h join bp_asset_space s on s.id=h.space_id "
                        + where + " order by h.house_code",
                args);
    }

    public List<Map<String, Object>> owners(Long projectId, Long houseId) {
        requireHouse(projectId, houseId);
        return jdbc.queryForList(
                "select ou.id, ou.person_id personId, p.person_name personName, p.phone, "
                        + "ou.relation_type relationType, ou.is_primary isPrimary, ou.status, "
                        + "ou.start_date startDate, ou.end_date endDate "
                        + "from prop_owner_unit ou join bp_person p on p.id=ou.person_id "
                        + "where ou.tenant_id=? and ou.house_id=? and ou.is_deleted=0 order by ou.is_primary desc, ou.id desc",
                TenantContext.tenantId(), houseId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> assignOwner(Long projectId, Long houseId, OwnerCmd cmd) {
        requireHouse(projectId, houseId);
        if (cmd.personId() == null) throw BizException.paramInvalid("请选择业主");
        if (cmd.isPrimary() == null || cmd.isPrimary() == 0) {
            // 允许非主业主
        } else {
            jdbc.update("update prop_owner_unit set is_primary=0, update_time=now() "
                    + "where tenant_id=? and house_id=? and is_deleted=0", TenantContext.tenantId(), houseId);
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_owner_unit(id,tenant_id,project_id,house_id,person_id,relation_type,"
                        + "is_primary,share_ratio,start_date,end_date,status,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?,?, 'ACTIVE',0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId, houseId, cmd.personId(),
                cmd.relationType() == null ? "OWNER" : cmd.relationType(),
                cmd.isPrimary() == null ? 0 : cmd.isPrimary(), cmd.shareRatio(),
                cmd.startDate() == null ? LocalDate.now() : cmd.startDate(), cmd.endDate(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> removeOwner(Long id) {
        int n = jdbc.update("update prop_owner_unit set is_deleted=1, update_time=now() "
                + "where id=? and tenant_id=?", id, TenantContext.tenantId());
        if (n == 0) throw BizException.notFound("业主关系");
        return Map.of("deleted", n);
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    private void requireHouse(Long projectId, Long houseId) {
        requireProject(projectId);
        Long n = jdbc.queryForObject("select count(*) from bp_asset_house "
                        + "where id=? and tenant_id=? and org_id=? and is_deleted=0",
                Long.class, houseId, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业房屋");
    }

    public record OwnerCmd(Long personId, String relationType, Integer isPrimary,
                           java.math.BigDecimal shareRatio, LocalDate startDate, LocalDate endDate) {
    }
}
