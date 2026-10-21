package com.yundao.bp.common.web;

import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * HTTP 入口的租户上下文设置。
 *
 * <p>执行顺序最高（{@code Ordered.HIGHEST_PRECEDENCE + 10}），保证业务代码拿到上下文。
 *
 * <p><b>⚠️ 当前为开发阶段实现</b>：从请求头读取 {@code X-Tenant-Id} / {@code X-User-Id}。
 * 生产必须改为从 <b>JWT</b> 解析，且
 * <b>不得采信前端传入的 tenantId</b>（否则等于没有隔离）。
 *
 * <p>放行：{@code /actuator/**}、{@code /api/callback/**}（回调自行反查租户）、
 * 登录相关接口。
 */
@Component
@Order(Integer.MIN_VALUE + 10)
public class TenantFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(TenantFilter.class);

    public static final String HDR_TENANT = "X-Tenant-Id";
    public static final String HDR_USER = "X-User-Id";

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String p = request.getRequestURI();
        return p.startsWith("/actuator")
                || p.startsWith("/api/callback")   // IoT 回调：自身按 lockId 反查租户
                || p.startsWith("/api/v1/auth")
                || p.equals("/error");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse resp, FilterChain chain)
            throws ServletException, IOException {
        String tenantId = trimToNull(req.getHeader(HDR_TENANT));
        String userId = trimToNull(req.getHeader(HDR_USER));
        try {
            if (tenantId != null) {
                Long uid = null;
                if (userId != null) {
                    try {
                        uid = Long.valueOf(userId);
                    } catch (NumberFormatException ignored) {
                        log.warn("非法 {}: {}", HDR_USER, userId);
                    }
                }
                TenantContext.set(TenantInfo.of(tenantId, uid));
            }
            chain.doFilter(req, resp);
        } finally {
            // ★ 必须清理：线程池复用会导致串租户
            TenantContext.clear();
        }
    }

    private String trimToNull(String s) {
        if (s == null) {
            return null;
        }
        String t = s.trim();
        return t.isEmpty() ? null : t;
    }
}
