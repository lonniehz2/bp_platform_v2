package com.yundao.platform.config;

import com.yundao.platform.common.tenant.TenantContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class TenantFilter extends OncePerRequestFilter {

    private final String defaultTenant;

    public TenantFilter(@Value("${bp.platform.default-tenant:350600}") String defaultTenant) {
        this.defaultTenant = defaultTenant;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String tenant = request.getHeader("X-Tenant-Id");
        TenantContext.set(tenant == null || tenant.isBlank() ? defaultTenant : tenant.trim());
        try {
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }
}
