package com.yundao.platform.config;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.tenant.TenantContext;
import com.yundao.platform.common.id.IdGenerator;
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
    private final IdGenerator idGen;

    public PermissionInterceptor(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
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
        if (!"GET".equalsIgnoreCase(request.getMethod())
                && !"HEAD".equalsIgnoreCase(request.getMethod())
                && !"OPTIONS".equalsIgnoreCase(request.getMethod())) {
            Long auditor = jdbc.queryForObject(
                    "select count(*) from bp_user_role ur join bp_role r on r.id=ur.role_id "
                            + "where ur.tenant_id=? and ur.user_id=? and r.role_code='AUDITOR'",
                    Long.class, TenantContext.require(), principal.userId());
            if (auditor != null && auditor > 0) {
                return deny(response, "BP40301", "只读角色不能执行写操作", 403);
            }
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
        String action = actionFor(path, request.getMethod());
        if (action != null && !actionAllowed(principal, menuCode, action)) {
            return deny(response, "BP40301", "无权限执行该操作", 403);
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        String path = request.getRequestURI();
        String method = request.getMethod();
        if (!path.startsWith("/api/v1/platform/")
                || "GET".equalsIgnoreCase(method) || "HEAD".equalsIgnoreCase(method)
                || "OPTIONS".equalsIgnoreCase(method)) {
            return;
        }
        UserContext.Principal principal = UserContext.get();
        if (principal == null) return;
        try {
            jdbc.update("insert into bp_audit_log(id,tenant_id,user_id,username,method,path,status_code,ip) "
                            + "values(?,?,?,?,?,?,?,?)",
                    idGen.nextId(), principal.tenantId(), principal.userId(), principal.username(),
                    method, path, response.getStatus(), request.getRemoteAddr());
        } catch (Exception ignored) {
            // 审计失败不阻断业务
        }
    }

    private String actionFor(String path, String method) {
        String m = method == null ? "" : method.toUpperCase();
        if ("GET".equals(m) || "HEAD".equals(m)) return "view";
        if ("OPTIONS".equals(m)) return null;
        String p = path.toLowerCase();
        if (p.contains("/approve") || p.contains("/reject") || p.contains("/resolve")
                || p.contains("/confirm") || p.contains("/pay") || p.contains("/refund")
                || p.contains("/terminate") || p.contains("/allocate") || p.contains("/publish")
                || p.contains("/checkout")) {
            return "approve";
        }
        if ("DELETE".equals(m)) return "delete";
        if ("PUT".equals(m) || "PATCH".equals(m) || p.contains("/update") || p.contains("/edit")) return "edit";
        if ("POST".equals(m)) return "create";
        return "edit";
    }

    private boolean actionAllowed(UserContext.Principal principal, String menuCode, String action) {
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) return true;
        Long configured = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=?",
                Long.class, principal.tenantId(), principal.userId(), menuCode);
        if (configured == null || configured == 0) return true;
        Long granted = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=? "
                        + "and ra.action_code in (?, '*')",
                Long.class, principal.tenantId(), principal.userId(), menuCode, action);
        return granted != null && granted > 0;
    }

    private String menuFor(String path) {
        if (path.startsWith("/api/v1/platform/users")
                || path.startsWith("/api/v1/platform/menus")
                || path.startsWith("/api/v1/platform/roles")) {
            return "rbac";
        }
        if (path.startsWith("/api/v1/platform/audit-logs")) return "audit";
        if (path.startsWith("/api/v1/platform/imports")) return "batchImport";
        if (path.startsWith("/api/v1/platform/messages")) return "message";
        if (path.startsWith("/api/v1/platform/open-apps")) return "sys";
        if (path.startsWith("/api/v1/platform/guarantee/short-rent-orders")) return "shortrent";
        if (path.startsWith("/api/v1/platform/guarantee/credits")) return "credit";
        if (path.startsWith("/api/v1/platform/guarantee/alerts")) return "alertCenter";
        if (path.startsWith("/api/v1/platform/guarantee/publicities")) return "publicities";
        if (path.startsWith("/api/v1/platform/guarantee/fee-items")) return "fee";
        if (path.startsWith("/api/v1/platform/guarantee/complaints")) return "complaints";
        if (path.startsWith("/api/v1/platform/guarantee/access-records")) return "accessRecords";
        if (path.startsWith("/api/v1/platform/guarantee/work-orders")) return "workOrders";
        if (path.startsWith("/api/v1/platform/guarantee/meters")) return "asset";
        if (path.startsWith("/api/v1/platform/guarantee/listings")
                || path.startsWith("/api/v1/platform/guarantee/bookings")) return "listings";
        if (path.startsWith("/api/v1/platform/projects")
                || path.startsWith("/api/v1/platform/space-templates")
                || path.startsWith("/api/v1/platform/asset-types")) return "asset";
        if (path.startsWith("/api/v1/platform/persons")) return "person";
        if (path.startsWith("/api/v1/platform/guarantee/applications")) return "applications";
        if (path.startsWith("/api/v1/platform/guarantee/waitlist")) return "waitlist";
        if (path.startsWith("/api/v1/platform/guarantee/allocations")) return "allocations";
        if (path.contains("/deposits")) return "deposits";
        if (path.contains("/subsidies")) return "subsidies";
        if (path.startsWith("/api/v1/platform/guarantee/contract-changes")) return "contractChanges";
        if (path.startsWith("/api/v1/platform/guarantee/qualification-reviews")) return "qualification";
        if (path.startsWith("/api/v1/platform/guarantee/contracts")) return "contracts";
        if (path.startsWith("/api/v1/platform/billing")) return "billing";
        if (path.startsWith("/api/v1/platform/devices")) return "devices";
        if (path.startsWith("/api/v1/platform/grants")) return "grants";
        if (path.startsWith("/api/v1/platform/workflows")
                || path.startsWith("/api/v1/platform/workflow-tasks")) return "audit";
        if (path.startsWith("/api/v1/platform/migration")) return "sys";
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
