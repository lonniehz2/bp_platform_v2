package com.yundao.bp.common.i18n;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Locale;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** HTTP 入口语言上下文；执行顺序在 TenantFilter 之后。 */
@Component
@Order(Integer.MIN_VALUE + 20)
public class LocaleFilter extends OncePerRequestFilter {

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String p = request.getRequestURI();
        return p.startsWith("/actuator") || p.startsWith("/api/callback") || p.equals("/error");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse resp,
                                    FilterChain chain) throws ServletException, IOException {
        Locale locale = LocaleSupport.fromRequest(req);
        try {
            LocaleContext.set(locale);
            resp.setHeader("Content-Language", LocaleContext.tag());
            chain.doFilter(req, resp);
        } finally {
            LocaleContext.clear();
        }
    }
}
