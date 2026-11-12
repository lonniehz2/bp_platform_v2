package com.yundao.platform.service;

import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ReceiptTemplateService {
    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public ReceiptTemplateService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list() {
        return jdbc.queryForList("select id, template_name templateName, config_json configJson, version, status, update_time updateTime from bp_receipt_template where tenant_id=? and is_deleted=0 order by id desc", TenantContext.require());
    }

    public Map<String, Object> create(String name, String configJson) {
        long id = idGen.nextId();
        jdbc.update("insert into bp_receipt_template(id,tenant_id,template_name,config_json,version,status,is_deleted) values(?,?,?,?,1,'DRAFT',0)", id, TenantContext.require(), name, configJson);
        return Map.of("id", id, "status", "DRAFT");
    }

    public List<Map<String, Object>> history(long id) {
        return jdbc.queryForList("select id, config_json configJson, version, create_time createTime from bp_receipt_template_version where tenant_id=? and template_id=? order by version desc", TenantContext.require(), id);
    }

    public Map<String, Object> update(long id, String name, String configJson) {
        List<Map<String, Object>> old = jdbc.queryForList("select config_json configJson, version from bp_receipt_template where id=? and tenant_id=? and is_deleted=0", id, TenantContext.require());
        if (!old.isEmpty()) {
            jdbc.update("insert into bp_receipt_template_version(id,tenant_id,template_id,config_json,version) values(?,?,?,?,?)",
                    idGen.nextId(), TenantContext.require(), id, old.get(0).get("configJson"), old.get(0).get("version"));
        }
        int n = jdbc.update("update bp_receipt_template set template_name=?, config_json=?, version=version+1, status='DRAFT' where id=? and tenant_id=? and is_deleted=0", name, configJson, id, TenantContext.require());
        if (n == 0) throw new IllegalArgumentException("模板不存在");
        return Map.of("id", id, "status", "DRAFT");
    }

    public Map<String, Object> rollback(long id, long versionId) {
        List<Map<String, Object>> rows = jdbc.queryForList("select config_json configJson, version from bp_receipt_template_version where id=? and tenant_id=? and template_id=?", versionId, TenantContext.require(), id);
        if (rows.isEmpty()) throw new IllegalArgumentException("版本不存在");
        List<Map<String, Object>> old = jdbc.queryForList("select config_json configJson, version from bp_receipt_template where id=? and tenant_id=? and is_deleted=0", id, TenantContext.require());
        if (!old.isEmpty()) {
            jdbc.update("insert into bp_receipt_template_version(id,tenant_id,template_id,config_json,version) values(?,?,?,?,?)", idGen.nextId(), TenantContext.require(), id, old.get(0).get("configJson"), old.get(0).get("version"));
        }
        jdbc.update("update bp_receipt_template set config_json=?, version=version+1, status='DRAFT' where id=? and tenant_id=? and is_deleted=0", rows.get(0).get("configJson"), id, TenantContext.require());
        return Map.of("id", id, "status", "DRAFT");
    }

    public Map<String, Object> publish(long id) {
        int n = jdbc.update("update bp_receipt_template set status='PUBLISHED' where id=? and tenant_id=? and is_deleted=0", id, TenantContext.require());
        if (n == 0) throw new IllegalArgumentException("模板不存在");
        return Map.of("id", id, "status", "PUBLISHED");
    }

    public record Cmd(String templateName, String configJson) {}
}
