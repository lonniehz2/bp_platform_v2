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
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) {
            return null;
        }
        Set<Long> ids = new LinkedHashSet<>(jdbc.queryForList(
                "select project_id from bp_user_project where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, TenantContext.require(), principal.userId()));
        return ids;
    }

    /**
     * 财务组织树范围：返回用户所属组织及其全部下级组织 ID。
     * 管理员返回 null，表示不限制。
     */
    public Set<Long> orgProjectIds() {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) {
            return null;
        }
        String tenant = TenantContext.require();
        Set<Long> roots = new LinkedHashSet<>(jdbc.queryForList(
                "select org_id from bp_user_org where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, tenant, principal.userId()));
        if (roots.isEmpty()) {
            return Set.of();
        }
        List<Map<String, Object>> orgs = jdbc.queryForList(
                "select id, parent_id parentId from bp_org where tenant_id=? and is_deleted=0", tenant);
        Map<Long, List<Long>> children = new HashMap<>();
        for (Map<String, Object> org : orgs) {
            if (org.get("parentId") == null) continue;
            long parent = ((Number) org.get("parentId")).longValue();
            children.computeIfAbsent(parent, k -> new java.util.ArrayList<>())
                    .add(((Number) org.get("id")).longValue());
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
