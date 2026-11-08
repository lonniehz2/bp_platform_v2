package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class MigrationExceptionService {

    private final JdbcTemplate jdbc;

    public MigrationExceptionService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> list(String status) {
        return jdbc.queryForList(
                "select id, source_table sourceTable, source_id sourceId, reason, payload, "
                        + "resolve_status resolveStatus, resolution, resolved_by resolvedBy, "
                        + "resolved_time resolvedTime, create_time createTime "
                        + "from bp_migration_exception where (? is null or resolve_status=?) "
                        + "order by id desc",
                status, status);
    }

    public Map<String, Object> resolve(long id, ResolveCmd cmd) {
        if (cmd.resolution() == null || cmd.resolution().isBlank()) {
            throw BizException.param("处理结论不能为空");
        }
        String user = UserContext.get() == null ? "system" : UserContext.get().displayName();
        long updated = jdbc.update(
                "update bp_migration_exception set resolve_status='RESOLVED', resolution=?, "
                        + "resolved_by=?, resolved_time=now() where id=? and resolve_status='PENDING'",
                cmd.resolution(), user, id);
        if (updated == 0) {
            throw BizException.notFound("异常记录不存在或已处理");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("resolveStatus", "RESOLVED");
        out.put("resolution", cmd.resolution());
        return out;
    }

    public record ResolveCmd(String resolution) {
    }
}
