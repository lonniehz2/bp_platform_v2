package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/audit-logs")
public class AuditLogController {

    private final JdbcTemplate jdbc;

    public AuditLogController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam(defaultValue = "100") int limit) {
        int size = Math.max(1, Math.min(limit, 500));
        return R.ok(jdbc.queryForList(
                "select id, user_id userId, username, method, path, status_code statusCode, ip, create_time createTime "
                        + "from bp_audit_log where tenant_id=? order by id desc limit ?",
                TenantContext.require(), size));
    }
}
