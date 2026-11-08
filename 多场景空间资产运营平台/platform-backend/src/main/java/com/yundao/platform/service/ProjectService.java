package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ProjectService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public ProjectService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list() {
        return jdbc.queryForList(
                "select o.id, o.org_code orgCode, o.org_name orgName, o.scene_code sceneCode, "
                        + "o.business_mode businessMode, o.space_template_id spaceTemplateId, "
                        + "t.template_name templateName, o.default_asset_type_code defaultAssetTypeCode, "
                        + "o.status, o.address, o.contact_name contactName, o.contact_phone contactPhone, o.remark, "
                        + "o.total_area totalArea, o.land_area landArea, o.property_type propertyType, o.build_year buildYear, "
                        + "o.create_time createTime, "
                        + "(select count(*) from guarantee_contract c where c.project_id=o.id and c.is_deleted=0) contractCount, "
                        + "(select count(*) from guarantee_application a where a.project_id=o.id and a.is_deleted=0) applicationCount, "
                        + "(select count(*) from bp_dev_device d where d.project_id=o.id and d.is_deleted=0) deviceCount "
                        + "from bp_org o left join bp_space_template t on t.id=o.space_template_id "
                        + "where o.tenant_id=? and o.is_deleted=0 order by o.id desc",
                TenantContext.require());
    }

    public Map<String, Object> create(ProjectCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.orgCode() == null || cmd.orgCode().isBlank()
                || cmd.orgName() == null || cmd.orgName().isBlank()) {
            throw BizException.param("项目编码和名称不能为空");
        }
        Long enabled = jdbc.queryForObject(
                "select count(*) from bp_tenant_scene where tenant_id=? and scene_code=? and status='ENABLED'",
                Long.class, tenant, cmd.sceneCode());
        if (enabled == null || enabled == 0) {
            throw BizException.param("租户未启用该场景");
        }
        Long mode = jdbc.queryForObject(
                "select count(*) from bp_business_mode where scene_code=? and mode_code=? and status='ENABLED'",
                Long.class, cmd.sceneCode(), cmd.businessMode());
        if (mode == null || mode == 0) {
            throw BizException.param("经营模式不属于该场景");
        }
        Long template = jdbc.queryForObject(
                "select count(*) from bp_space_template where id=? and tenant_id=? and scene_code=? "
                        + "and status='ENABLED' and is_deleted=0",
                Long.class, cmd.spaceTemplateId(), tenant, cmd.sceneCode());
        if (template == null || template == 0) {
            throw BizException.param("空间模板不属于该场景或不可用");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_org(id,tenant_id,parent_id,org_code,org_name,org_type,"
                            + "scene_code,business_mode,space_template_id,default_asset_type_code,"
                            + "address,contact_name,contact_phone,remark,"
                            + "total_area,land_area,property_type,build_year,"
                            + "org_path,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,?,?,?,?,?,0,'ENABLED',0)",
                    id, tenant, cmd.parentId(), cmd.orgCode().trim(), cmd.orgName().trim(),
                    cmd.sceneCode(), cmd.businessMode(), cmd.spaceTemplateId(),
                    cmd.defaultAssetTypeCode(), cmd.address(), cmd.contactName(), cmd.contactPhone(),
                    cmd.remark(), cmd.totalArea(), cmd.landArea(), cmd.propertyType(), cmd.buildYear(),
                    "/" + id + "/");
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("项目编码已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("orgCode", cmd.orgCode());
        out.put("sceneCode", cmd.sceneCode());
        out.put("businessMode", cmd.businessMode());
        return out;
    }

    public record ProjectCmd(String orgCode, String orgName, Long parentId, String sceneCode,
                             String businessMode, Long spaceTemplateId,
                             String defaultAssetTypeCode, String address,
                             String contactName, String contactPhone, String remark,
                             java.math.BigDecimal totalArea, java.math.BigDecimal landArea,
                             String propertyType, Integer buildYear) {
    }
}
