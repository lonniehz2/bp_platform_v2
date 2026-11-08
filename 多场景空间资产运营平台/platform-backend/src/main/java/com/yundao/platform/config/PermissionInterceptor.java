package com.yundao.platform.config;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.tenant.TenantContext;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class PermissionInterceptor implements HandlerInterceptor {

    private final JdbcTemplate jdbc;

    public PermissionInterceptor(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        String path = request.getRequestURI();
        if (!path.startsWith("/api/v1/platform/")) {
            return true;
        }
        String menuCode = menuFor(path);
        if (menuCode == null) {
            return true;
        }
        UserContext.Principal principal = UserContext.get();
        if (principal == null) {
            return deny(response, "BP40100", "未登录或登录已过期", 401);
        }
        Long count = jdbc.queryForObject(
                "select count(*) from bp_user_role ur "
                        + "join bp_role_menu rm on rm.role_id=ur.role_id "
                        + "join bp_menu m on m.id=rm.menu_id "
                        + "where ur.tenant_id=? and ur.user_id=? and m.scene_code='GUARANTEE' "
                        + "and m.menu_code=? and m.menu_status='ENABLED'",
                Long.class, TenantContext.require(), principal.userId(), menuCode);
        if (count == null || count == 0) {
            return deny(response, "BP40300", "无权访问该功能", 403);
        }
        return true;
    }

    private String menuFor(String path) {
        if (path.startsWith("/api/v1/platform/guarantee/alerts")) {
            return "alert";
        }
        if (path.startsWith("/api/v1/platform/guarantee/publicities")) {
            return "publicity";
        }
        if (path.startsWith("/api/v1/platform/guarantee/fee-items")) {
            return "billing";
        }
        if (path.startsWith("/api/v1/platform/guarantee/complaints")) {
            return "complaint";
        }
        if (path.startsWith("/api/v1/platform/guarantee/access-records")) {
            return "access";
        }
        if (path.startsWith("/api/v1/platform/guarantee/work-orders")) {
            return "service";
        }
        if (path.startsWith("/api/v1/platform/guarantee/meters")) {
            return "asset";
        }
        if (path.startsWith("/api/v1/platform/projects")
                || path.startsWith("/api/v1/platform/space-templates")
                || path.startsWith("/api/v1/platform/asset-types")) {
            return "asset";
        }
        if (path.startsWith("/api/v1/platform/persons")) {
            return "person";
        }
        if (path.startsWith("/api/v1/platform/guarantee/applications")
                || path.startsWith("/api/v1/platform/guarantee/waitlist")
                || path.startsWith("/api/v1/platform/guarantee/allocations")) {
            return "application";
        }
        if (path.contains("/deposit") || path.contains("/subsidies")) {
            return "billing";
        }
        if (path.startsWith("/api/v1/platform/guarantee/contracts")
                || path.startsWith("/api/v1/platform/guarantee/contract-changes")
                || path.startsWith("/api/v1/platform/guarantee/qualification-reviews")) {
            return "contract";
        }
        if (path.startsWith("/api/v1/platform/guarantee/deposits")
                || path.startsWith("/api/v1/platform/guarantee/subsidies")
                || path.startsWith("/api/v1/platform/billing")) {
            return "billing";
        }
        if (path.startsWith("/api/v1/platform/devices")
                || path.startsWith("/api/v1/platform/grants")) {
            return "device";
        }
        if (path.startsWith("/api/v1/platform/workflows")
                || path.startsWith("/api/v1/platform/workflow-tasks")) {
            return "audit";
        }
        if (path.startsWith("/api/v1/platform/menus")
                || path.startsWith("/api/v1/platform/roles")) {
            return "config";
        }
        if (path.startsWith("/api/v1/platform/migration")) {
            return "system";
        }
        return null;
    }

    private boolean deny(HttpServletResponse response, String code, String message, int status)
            throws Exception {
        response.setStatus(status);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":\"" + code + "\",\"message\":\"" + message + "\","
                + "\"data\":null,\"timestamp\":" + System.currentTimeMillis() + "}");
        return false;
    }
}
