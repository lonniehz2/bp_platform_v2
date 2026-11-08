package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashSet;
import java.util.List;
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
}
