package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * 过渡期动作权限：按角色编码授予动作权限。
 * 正式版本应迁移到 bp_role_permission 表。
 */
@Service
public class PermissionService {

    private final JdbcTemplate jdbc;

    public PermissionService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public java.util.Set<String> permissions() {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        java.util.Set<String> out = new java.util.LinkedHashSet<>();
        for (String role : roles) out.addAll(grants(role));
        return out;
    }

    public void require(String permission) {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        Set<String> granted = roles.stream().flatMap(r -> grants(r).stream()).collect(Collectors.toSet());
        boolean allowed = granted.contains("*")
                || granted.contains(permission)
                || granted.stream().anyMatch(p -> p.endsWith(":*")
                && permission.startsWith(p.substring(0, p.length() - 1)));
        if (!allowed) {
            throw new BizException("BP40301", "无权限执行该操作", 403);
        }
    }

    private List<String> grants(String role) {
        return switch (role) {
            case "GUARANTEE_ADMIN", "ADMIN" -> List.of("*");
            case "CONTRACT_CLERK" -> List.of("contract:*", "billing:view", "billing:pay");
            case "ASSET_CLERK" -> List.of("device:*", "house:*", "space:*", "allocation:*");
            case "SERVICE_CLERK" -> List.of("complaint:*", "visit:*");
            case "AUDITOR" -> List.of("*:view");
            case "GUARANTEE_FINANCE", "FINANCE" -> List.of("billing:*", "deposit:*", "subsidy:*", "contract:view");
            case "STAFF" -> List.of("application:*", "contract:view", "billing:view");
            case "TENANT" -> List.of("self");
            default -> List.of();
        };
    }
}
