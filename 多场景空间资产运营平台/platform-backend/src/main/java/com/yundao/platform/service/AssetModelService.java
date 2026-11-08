package com.yundao.platform.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class AssetModelService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final ObjectMapper objectMapper;

    public AssetModelService(JdbcTemplate jdbc, IdGenerator idGen, ObjectMapper objectMapper) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.objectMapper = objectMapper;
    }

    public List<Map<String, Object>> templates(String sceneCode) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, scene_code sceneCode, template_code templateCode, template_name templateName, "
                        + "base_level_count baseLevelCount, level_count levelCount, levels_json levelsJson, "
                        + "allowed_sub_modes allowedSubModes, version_no versionNo, status "
                        + "from bp_space_template where tenant_id=? "
                        + "and (? is null or scene_code=?) and is_deleted=0 "
                        + "order by scene_code, template_code, version_no desc",
                TenantContext.require(), sceneCode, sceneCode);
        rows.forEach(this::decodeLevels);
        return rows;
    }

    public Map<String, Object> createTemplate(TemplateCmd cmd) {
        String tenant = TenantContext.require();
        requireScene(cmd.sceneCode());
        if (cmd.templateCode() == null || cmd.templateCode().isBlank()
                || cmd.templateName() == null || cmd.templateName().isBlank()) {
            throw BizException.param("模板编码和名称不能为空");
        }
        int baseCount = cmd.baseLevelCount() == null ? 0 : cmd.baseLevelCount();
        if (baseCount < 2 || baseCount > 6) {
            throw BizException.param("基础层级必须在 2 到 6 之间");
        }
        if (cmd.levels() == null || cmd.levels().size() < baseCount) {
            throw BizException.param("层级配置少于基础层级数");
        }
        List<Level> levels = new ArrayList<>();
        for (int i = 0; i < cmd.levels().size(); i++) {
            Level level = cmd.levels().get(i);
            if (level.name() == null || level.name().isBlank()) {
                throw BizException.param("第 " + (i + 1) + " 级名称不能为空");
            }
            levels.add(new Level(i + 1, level.name().trim(),
                    level.required() == null || level.required()));
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_space_template(id,tenant_id,scene_code,template_code,template_name,"
                            + "asset_type_code,base_level_count,level_count,levels_json,allowed_sub_modes,"
                            + "is_system,version_no,status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,0,1,'ENABLED',0)",
                    id, tenant, cmd.sceneCode(), cmd.templateCode().trim(), cmd.templateName().trim(),
                    cmd.assetTypeCode(), baseCount, levels.size(),
                    objectMapper.writeValueAsString(levels),
                    cmd.allowedSubModes() == null ? "NONE" : cmd.allowedSubModes());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("模板编码已存在");
        } catch (Exception e) {
            throw BizException.param("层级 JSON 生成失败");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("templateCode", cmd.templateCode());
        return out;
    }

    public List<Map<String, Object>> assetTypes(String sceneCode) {
        return jdbc.queryForList(
                "select id, scene_code sceneCode, type_code typeCode, type_name typeName, "
                        + "type_category typeCategory, sort_no sortNo, status "
                        + "from bp_asset_type where tenant_id=? "
                        + "and (? is null or scene_code=?) and is_deleted=0 "
                        + "order by scene_code, type_category, sort_no, type_code",
                TenantContext.require(), sceneCode, sceneCode);
    }

    public Map<String, Object> createAssetType(AssetTypeCmd cmd) {
        String tenant = TenantContext.require();
        requireScene(cmd.sceneCode());
        if (cmd.typeCode() == null || cmd.typeCode().isBlank()
                || cmd.typeName() == null || cmd.typeName().isBlank()) {
            throw BizException.param("资产类型编码和名称不能为空");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_asset_type(id,tenant_id,scene_code,type_code,type_name,"
                            + "type_category,sort_no,status,is_deleted) values(?,?,?,?,?,?,?,'ENABLED',0)",
                    id, tenant, cmd.sceneCode(), cmd.typeCode().trim(), cmd.typeName().trim(),
                    cmd.typeCategory() == null ? "HOUSE" : cmd.typeCategory(),
                    cmd.sortNo() == null ? 0 : cmd.sortNo());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("资产类型编码已存在");
        }
        return Map.of("id", id, "typeCode", cmd.typeCode());
    }

    private void decodeLevels(Map<String, Object> row) {
        Object json = row.remove("levelsJson");
        if (json == null) {
            row.put("levels", List.of());
            return;
        }
        try {
            row.put("levels", objectMapper.readValue(String.valueOf(json),
                    new TypeReference<List<Level>>() {
                    }));
        } catch (Exception e) {
            row.put("levels", List.of());
        }
    }

    private void requireScene(String sceneCode) {
        Long count = jdbc.queryForObject(
                "select count(*) from bp_scene_profile where scene_code=? and status='ENABLED'",
                Long.class, sceneCode);
        if (count == null || count == 0) {
            throw BizException.notFound("场景不存在");
        }
    }

    public record Level(Integer level, String name, Boolean required) {
    }

    public record TemplateCmd(String sceneCode, String templateCode, String templateName,
                              String assetTypeCode, Integer baseLevelCount, List<Level> levels,
                              String allowedSubModes) {
    }

    public record AssetTypeCmd(String sceneCode, String typeCode, String typeName,
                               String typeCategory, Integer sortNo) {
    }
}
