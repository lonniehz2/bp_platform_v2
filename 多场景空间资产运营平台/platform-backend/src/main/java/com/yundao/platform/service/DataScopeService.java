package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * 数据范围：管理员返回 null 表示不限制，其他用户返回已授权项目集合。
 */
@Service
public class DataScopeService {

    private final JdbcTemplate jdbc;

    public DataScopeService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Set<Long> projectIds() {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = roles(principal);
        if (isUnrestricted(roles)) return null;
        List<Map<String, Object>> scopes = jdbc.queryForList(
                "select rs.scope_type scopeType from bp_role_scope rs join bp_role r on r.id=rs.role_id "
                        + "where rs.tenant_id=? and r.role_code in (" + placeholders(roles) + ")",
                args(principal.tenantId(), roles));
        if (scopes.isEmpty()) return legacyProjects(principal);
        if (scopes.stream().anyMatch(r -> "ALL".equals(r.get("scopeType")))) return null;
        Set<Long> ids = new LinkedHashSet<>();
        for (String role : roles) {
            List<Map<String, Object>> r = jdbc.queryForList(
                    "select rs.scope_type scopeType from bp_role_scope rs join bp_role ro on ro.id=rs.role_id "
                            + "where rs.tenant_id=? and ro.role_code=?", principal.tenantId(), role);
            if (r.isEmpty()) continue;
            String type = String.valueOf(r.get(0).get("scopeType"));
            if ("PROJECTS".equals(type)) {
                ids.addAll(jdbc.queryForList("select rp.project_id from bp_role_project rp join bp_role ro on ro.id=rp.role_id "
                        + "where ro.role_code=? and ro.tenant_id=?", Long.class, role, principal.tenantId()));
            } else if ("ORGS".equals(type)) {
                ids.addAll(jdbc.queryForList("select rp.org_id from bp_role_org rp join bp_role ro on ro.id=rp.role_id "
                        + "where ro.role_code=? and ro.tenant_id=?", Long.class, role, principal.tenantId()));
            }
        }
        if (overrideEnabled(principal)) {
            ids.retainAll(legacyProjects(principal));
        }
        return ids;
    }

    public Set<Long> orgProjectIds() {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = roles(principal);
        if (isUnrestricted(roles)) return null;
        List<Map<String, Object>> scopes = jdbc.queryForList(
                "select rs.scope_type scopeType from bp_role_scope rs join bp_role r on r.id=rs.role_id "
                        + "where rs.tenant_id=? and r.role_code in (" + placeholders(roles) + ")",
                args(principal.tenantId(), roles));
        if (scopes.isEmpty()) return legacyOrgs(principal);
        if (scopes.stream().anyMatch(r -> "ALL".equals(r.get("scopeType")))) return null;
        Set<Long> roots = new LinkedHashSet<>();
        for (String role : roles) {
            List<Map<String, Object>> r = jdbc.queryForList(
                    "select rs.scope_type scopeType from bp_role_scope rs join bp_role ro on ro.id=rs.role_id "
                            + "where rs.tenant_id=? and ro.role_code=?", principal.tenantId(), role);
            if (r.isEmpty()) continue;
            String type = String.valueOf(r.get(0).get("scopeType"));
            if ("PROJECTS".equals(type)) {
                roots.addAll(jdbc.queryForList("select rp.project_id from bp_role_project rp join bp_role ro on ro.id=rp.role_id "
                        + "where ro.role_code=? and ro.tenant_id=?", Long.class, role, principal.tenantId()));
            } else if ("ORGS".equals(type)) {
                roots.addAll(jdbc.queryForList("select rp.org_id from bp_role_org rp join bp_role ro on ro.id=rp.role_id "
                        + "where ro.role_code=? and ro.tenant_id=?", Long.class, role, principal.tenantId()));
            }
        }
        Set<Long> expanded = expandOrgs(roots);
        if (overrideEnabled(principal)) {
            expanded.retainAll(legacyOrgs(principal));
        }
        return expanded;
    }

    private Set<Long> legacyProjects(UserContext.Principal p) {
        return new LinkedHashSet<>(jdbc.queryForList(
                "select project_id from bp_user_project where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, TenantContext.require(), p.userId()));
    }

    private Set<Long> legacyOrgs(UserContext.Principal p) {
        Set<Long> roots = new LinkedHashSet<>(jdbc.queryForList(
                "select org_id from bp_user_org where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, TenantContext.require(), p.userId()));
        return expandOrgs(roots);
    }

    private boolean overrideEnabled(UserContext.Principal p) {
        List<Integer> rows = jdbc.queryForList(
                "select enabled from bp_user_scope_override where tenant_id=? and user_id=?",
                Integer.class, TenantContext.require(), p.userId());
        return !rows.isEmpty() && rows.get(0) != null && rows.get(0) == 1;
    }

    private List<String> roles(UserContext.Principal p) {
        return jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, p.tenantId(), p.userId());
    }

    private boolean isUnrestricted(List<String> roles) {
        return roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN") || roles.contains("AUDITOR");
    }

    private static String placeholders(List<String> values) {
        return String.join(",", java.util.Collections.nCopies(values.size(), "?"));
    }

    private static Object[] args(String tenant, List<String> roles) {
        Object[] out = new Object[roles.size() + 1];
        out[0] = tenant;
        for (int i = 0; i < roles.size(); i++) out[i + 1] = roles.get(i);
        return out;
    }

    private Set<Long> expandOrgs(Set<Long> roots) {
        if (roots.isEmpty()) return Set.of();
        String tenant = TenantContext.require();
        List<Map<String, Object>> orgs = jdbc.queryForList(
                "select id, parent_id parentId from bp_org where tenant_id=? and is_deleted=0", tenant);
        Map<Long, List<Long>> children = new HashMap<>();
        for (Map<String, Object> org : orgs) {
            if (org.get("parentId") == null) continue;
            long parent = ((Number) org.get("parentId")).longValue();
            children.computeIfAbsent(parent, k -> new java.util.ArrayList<>()).add(((Number) org.get("id")).longValue());
        }
        Set<Long> out = new LinkedHashSet<>();
        java.util.ArrayDeque<Long> queue = new java.util.ArrayDeque<>(roots);
        while (!queue.isEmpty()) {
            long id = queue.removeFirst();
            if (!out.add(id)) continue;
            queue.addAll(children.getOrDefault(id, List.of()));
        }
        return out;
    }

    public void requireProject(long projectId) {
        Set<Long> ids = orgProjectIds();
        if (ids != null && !ids.contains(projectId)) {
            throw new BizException("BP40302", "无权访问该项目数据", 403);
        }
    }
}
