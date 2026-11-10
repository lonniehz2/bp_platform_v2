package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RoleScopeService {

    private final JdbcTemplate jdbc;

    public RoleScopeService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> get(long roleId) {
        String tenant = TenantContext.require();
        requireRole(roleId, tenant);
        Map<String, Object> out = new LinkedHashMap<>();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select scope_type scopeType from bp_role_scope where role_id=? and tenant_id=?", roleId, tenant);
        out.put("roleId", roleId);
        out.put("scopeType", rows.isEmpty() ? "NONE" : rows.get(0).get("scopeType"));
        out.put("projectIds", jdbc.queryForList(
                "select project_id from bp_role_project where role_id=?", Long.class, roleId));
        out.put("orgIds", jdbc.queryForList(
                "select org_id from bp_role_org where role_id=?", Long.class, roleId));
        return out;
    }

    @Transactional
    public Map<String, Object> save(long roleId, ScopeCmd cmd) {
        String tenant = TenantContext.require();
        requireRole(roleId, tenant);
        String type = cmd.scopeType() == null ? "NONE" : cmd.scopeType();
        if (!List.of("ALL", "PROJECTS", "ORGS", "SELF", "NONE").contains(type)) {
            throw BizException.param("数据范围类型不合法");
        }
        jdbc.update("insert into bp_role_scope(role_id,tenant_id,scope_type) values(?,?,?) "
                + "on duplicate key update scope_type=values(scope_type)", roleId, tenant, type);
        jdbc.update("delete from bp_role_project where role_id=?", roleId);
        jdbc.update("delete from bp_role_org where role_id=?", roleId);
        if (cmd.projectIds() != null) {
            for (Long projectId : cmd.projectIds()) {
                Long count = jdbc.queryForObject("select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0", Long.class, projectId, tenant);
                if (count == null || count == 0) throw BizException.param("项目不合法");
                jdbc.update("insert into bp_role_project(role_id,project_id) values(?,?)", roleId, projectId);
            }
        }
        if (cmd.orgIds() != null) {
            for (Long orgId : cmd.orgIds()) {
                Long count = jdbc.queryForObject("select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0", Long.class, orgId, tenant);
                if (count == null || count == 0) throw BizException.param("组织不合法");
                jdbc.update("insert into bp_role_org(role_id,org_id) values(?,?)", roleId, orgId);
            }
        }
        return get(roleId);
    }


    public java.util.Map<String, Object> actions(long roleId) {
        String tenant = TenantContext.require();
        requireRole(roleId, tenant);
        return java.util.Map.of("roleId", roleId,
                "actions", jdbc.queryForList("select action_code from bp_role_action where role_id=?", String.class, roleId));
    }

    @Transactional
    public java.util.Map<String, Object> saveActions(long roleId, java.util.List<String> actions) {
        String tenant = TenantContext.require();
        requireRole(roleId, tenant);
        jdbc.update("delete from bp_role_action where role_id=?", roleId);
        if (actions != null) {
            for (String code : actions) {
                if (code == null || code.isBlank()) continue;
                jdbc.update("insert ignore into bp_role_action(role_id,action_code) values(?,?)", roleId, code);
            }
        }
        return actions(roleId);
    }

    private void requireRole(long roleId, String tenant) {
        Long count = jdbc.queryForObject("select count(*) from bp_role where id=? and tenant_id=? and is_deleted=0", Long.class, roleId, tenant);
        if (count == null || count == 0) throw BizException.notFound("角色不存在");
    }

    public record ScopeCmd(String scopeType, List<Long> projectIds, List<Long> orgIds) { }
}
