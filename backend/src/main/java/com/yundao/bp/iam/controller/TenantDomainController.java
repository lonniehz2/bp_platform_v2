package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.R;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 公开租户域名解析：登录页根据子域名预填租户号。 */
@RestController
@RequestMapping("/api/v1/public/tenant")
public class TenantDomainController {

    private final JdbcTemplate jdbc;

    public TenantDomainController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping("/by-domain")
    public R<Map<String, Object>> byDomain(@RequestParam String domain) {
        String normalized = domain == null ? "" : domain.trim().toLowerCase();
        if (normalized.endsWith(".")) normalized = normalized.substring(0, normalized.length() - 1);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select d.domain, d.tenant_id tenantId, t.tenant_code tenantCode, t.tenant_name tenantName "
                        + "from bp_iam_tenant_domain d join bp_iam_tenant t on t.tenant_code=d.tenant_id "
                        + "where d.domain=? and d.status='ENABLED' and t.status='ENABLED' and t.is_deleted=0 limit 1",
                normalized);
        if (rows.isEmpty()) return R.ok(null);
        Map<String, Object> out = new LinkedHashMap<>(rows.get(0));
        out.put("domain", normalized);
        return R.ok(out);
    }
}
