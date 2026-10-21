package com.yundao.bp.iam.security;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.service.AuthService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 认证与鉴权拦截器。
 *
 * <p><b>职责</b>：
 * <ol>
 *   <li>校验 `Authorization: Bearer &lt;token&gt;`（或 `X-Token`）</li>
 *   <li>加载会话 → 写入 {@link LoginUser} 与租户上下文</li>
 *   <li>若接口标注 {@link RequirePerm}，校验权限</li>
 * </ol>
 *
 * <p><b>放行白名单</b>：登录接口、健康检查、静态资源。
 *
 * <p><b>演示兼容</b>：当 {@code bp.security.enabled=false} 时退化为
 * 「信任 X-Tenant-Id / X-User-Id 请求头」的开发模式（**仅限本地演示**）。
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(AuthInterceptor.class);
    private static final ObjectMapper JSON = new ObjectMapper();

    private final AuthService authService;
    private final boolean securityEnabled;

    public AuthInterceptor(AuthService authService,
                           @Value("${bp.security.enabled:true}") boolean securityEnabled) {
        this.authService = authService;
        this.securityEnabled = securityEnabled;
        log.info("认证拦截器已启用，security.enabled={}", securityEnabled);
    }

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse resp, Object handler)
            throws Exception {
        // 放行：预检请求
        if ("OPTIONS".equalsIgnoreCase(req.getMethod())) {
            return true;
        }
        String path = req.getRequestURI();
        // 放行：登录、健康检查
        if (path.startsWith("/api/v1/auth/login") || path.startsWith("/actuator/")
                || path.equals("/") || path.startsWith("/index.html")
                || path.startsWith("/favicon") || path.startsWith("/error")) {
            return true;
        }

        // 非 API 请求不影响（静态资源）
        if (!path.startsWith("/api/")) {
            return true;
        }

        // 开发模式：信任请求头（仅本地演示，生产必须关闭 bp.security.enabled）
        if (!securityEnabled) {
            String tid = req.getHeader("X-Tenant-Id");
            String uid = req.getHeader("X-User-Id");
            if (tid != null && !tid.isBlank()) {
                Long userId = uid == null || uid.isBlank() ? null : Long.valueOf(uid);
                TenantContext.set(TenantInfo.of(tid, userId));
                LoginUser.set(new LoginUser(userId, "dev", "开发模式", tid, null, true,
                        "dev-token", java.util.Set.of("*")));
            }
            return true;
        }

        String token = extractToken(req);
        LoginUser user = authService.loadByToken(token);
        if (user == null) {
            reject(resp, 401, ErrorCode.UNAUTHORIZED,
                    "未登录或登录已过期，请重新登录");
            return false;
        }

        // 租户上下文（多租户隔离必需）
        TenantContext.set(TenantInfo.of(user.tenantId(), user.userId()));
        LoginUser.set(user);

        // 权限校验
        RequirePerm perm = resolvePerm(handler);
        if (perm != null && !user.has(perm.value())) {
            log.warn("权限不足：user={} 需要={} 路径={}", user.username(), perm.value(), path);
            reject(resp, 403, ErrorCode.FORBIDDEN,
                    "无操作权限（需要权限：" + perm.value() + "）");
            return false;
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse resp, Object handler,
                                Exception ex) {
        TenantContext.clear();
        LoginUser.clear();
    }

    /** 方法级优先，其次类级。 */
    private static RequirePerm resolvePerm(Object handler) {
        if (!(handler instanceof HandlerMethod hm)) {
            return null;
        }
        RequirePerm m = hm.getMethodAnnotation(RequirePerm.class);
        if (m != null) {
            return m;
        }
        return hm.getBeanType().getAnnotation(RequirePerm.class);
    }

    private static String extractToken(HttpServletRequest req) {
        String auth = req.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            return auth.substring(7).trim();
        }
        String t = req.getHeader("X-Token");
        return t == null ? null : t.trim();
    }

    private static void reject(HttpServletResponse resp, int httpStatus, ErrorCode code,
                               String msg) throws Exception {
        resp.setStatus(httpStatus);
        resp.setContentType("application/json;charset=UTF-8");
        R<Void> body = R.fail(code, msg);
        resp.getOutputStream().write(
                JSON.writeValueAsString(body).getBytes(StandardCharsets.UTF_8));
    }
}
