package com.yundao.platform.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SpaceService {

    private static final List<String> SPACE_TYPES = List.of(
            "AREA", "BUILDING", "UNIT", "FLOOR", "ROOM", "INNER_ROOM", "BED", "SITE", "PARKING");

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final ObjectMapper objectMapper;

    public SpaceService(JdbcTemplate jdbc, IdGenerator idGen, ObjectMapper objectMapper) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.objectMapper = objectMapper;
    }

    public List<Map<String, Object>> list(long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, parent_id parentId, space_code spaceCode, space_name spaceName, "
                        + "space_type spaceType, space_path spacePath, level_no levelNo, "
                        + "asset_type_code assetTypeCode, sub_unit_mode subUnitMode, area, status "
                        + "from bp_space where tenant_id=? and org_id=? and is_deleted=0 "
                        + "order by level_no, sort_no, id",
                TenantContext.require(), projectId);
    }

    @Transactional
    public Map<String, Object> create(long projectId, SpaceCmd cmd) {
        String tenant = TenantContext.require();
        Project project = requireProject(projectId);
        if (cmd.spaceCode() == null || cmd.spaceCode().isBlank()
                || cmd.spaceName() == null || cmd.spaceName().isBlank()) {
            throw BizException.param("空间编码和名称不能为空");
        }
        if (!SPACE_TYPES.contains(cmd.spaceType())) {
            throw BizException.param("空间类型不合法");
        }
        Template template = template(project.spaceTemplateId());
        int levelNo = 1;
        String path = "/" + cmd.spaceCode().trim();
        if (cmd.parentId() != null) {
            Map<String, Object> parent = jdbc.queryForMap(
                    "select id, level_no levelNo, space_path spacePath, sub_unit_mode subUnitMode "
                            + "from bp_space where id=? and tenant_id=? and org_id=? and is_deleted=0",
                    cmd.parentId(), tenant, projectId);
            levelNo = ((Number) parent.get("levelNo")).intValue() + 1;
            path = String.valueOf(parent.get("spacePath")) + "/" + cmd.spaceCode().trim();
        }
        if (levelNo > template.baseLevelCount() + 2) {
            throw BizException.param("空间层级超过模板允许范围");
        }
        if (levelNo > template.baseLevelCount()
                && !List.of("INNER_ROOM", "BED").contains(cmd.spaceType())) {
            throw BizException.param("超出基础层级的只能是内房或床位");
        }
        if (cmd.assetTypeCode() != null && !cmd.assetTypeCode().isBlank()) {
            Long count = jdbc.queryForObject(
                    "select count(*) from bp_asset_type where tenant_id=? and scene_code=? "
                            + "and type_code=? and status='ENABLED' and is_deleted=0",
                    Long.class, tenant, project.sceneCode(), cmd.assetTypeCode());
            if (count == null || count == 0) {
                throw BizException.param("资产类型不属于当前场景");
            }
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_space(id,tenant_id,org_id,parent_id,space_code,space_name,"
                            + "space_type,space_path,level_no,asset_type_code,space_template_id,"
                            + "business_mode,sub_unit_mode,area,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'ENABLED',0)",
                    id, tenant, projectId, cmd.parentId(), cmd.spaceCode().trim(), cmd.spaceName().trim(),
                    cmd.spaceType(), path, levelNo, cmd.assetTypeCode(), project.spaceTemplateId(),
                    project.businessMode(), cmd.subUnitMode(), cmd.area(), cmd.sortNo() == null ? 0 : cmd.sortNo());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("同一项目下空间编码已存在");
        }
        Long houseId = null;
        if (Boolean.TRUE.equals(cmd.rentable())) {
            if (!List.of("ROOM", "INNER_ROOM", "BED").contains(cmd.spaceType())) {
                throw BizException.param("只有房屋、内房、床位可以作为出租单元");
            }
            houseId = idGen.nextId();
            try {
                jdbc.update("insert into bp_house(id,tenant_id,org_id,space_id,house_code,house_name,"
                                + "asset_type_code,area,inner_area,house_status,is_deleted) "
                                + "values(?,?,?,?,?,?,?,?,?, 'VACANT',0)",
                        houseId, tenant, projectId, id, cmd.spaceCode().trim(), cmd.spaceName().trim(),
                        cmd.assetTypeCode(), cmd.area(), cmd.innerArea());
            } catch (DataIntegrityViolationException e) {
                throw BizException.conflict("该空间已存在房源");
            }
        }
        return Map.of("id", id, "houseId", houseId == null ? "" : houseId, "levelNo", levelNo);
    }

    private Project requireProject(long projectId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, scene_code sceneCode, business_mode businessMode, space_template_id spaceTemplateId "
                        + "from bp_org where id=? and tenant_id=? and is_deleted=0",
                projectId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("项目不存在");
        }
        Map<String, Object> row = rows.get(0);
        Object templateId = row.get("spaceTemplateId");
        if (templateId == null) {
            throw BizException.param("项目未选择空间模板");
        }
        return new Project(((Number) row.get("id")).longValue(),
                String.valueOf(row.get("sceneCode")),
                String.valueOf(row.get("businessMode")),
                ((Number) templateId).longValue());
    }

    private Template template(long templateId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select base_level_count baseLevelCount, levels_json levelsJson, allowed_sub_modes allowedSubModes "
                        + "from bp_space_template where id=? and tenant_id=? and status='ENABLED' and is_deleted=0",
                templateId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.param("空间模板不存在");
        }
        Map<String, Object> row = rows.get(0);
        int base = ((Number) row.get("baseLevelCount")).intValue();
        return new Template(base, String.valueOf(row.get("allowedSubModes")));
    }

    private record Project(long id, String sceneCode, String businessMode, long spaceTemplateId) {
    }

    private record Template(int baseLevelCount, String allowedSubModes) {
    }

    public record SpaceCmd(Long parentId, String spaceCode, String spaceName, String spaceType,
                           String assetTypeCode, String subUnitMode, Double area, Double innerArea,
                           Boolean rentable, Integer sortNo) {
    }
}
