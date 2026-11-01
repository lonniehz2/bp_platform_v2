package com.yundao.bp.common.i18n;

import com.yundao.bp.common.tenant.TenantContext;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 业务主数据翻译（组织名、房源名、人员姓名等）。
 *
 * <p>翻译存放在 {@code sys_i18n_text}，按「资源类型 + 资源ID + 字段 + 语言」唯一。
 * 展示层通过 {@code DisplayEnricher} 覆盖列表里的名称字段，因此不需要逐个接口改造。</p>
 */
@Service
public class I18nTextService {

    private final JdbcTemplate jdbc;
    private final Map<String, Map<String, String>> cache = new java.util.concurrent.ConcurrentHashMap<>();

    public I18nTextService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    private static String key(String type, long id, String field) {
        return type + ":" + id + ":" + field;
    }

    /** 当前租户 + 语言的全部翻译；找不到租户时返回空表（公开页不翻译业务数据）。 */
    public Map<String, String> all(String locale) {
        String tenant;
        try {
            tenant = TenantContext.tenantId();
        } catch (RuntimeException e) {
            return Map.of();
        }
        String cacheKey = tenant + "|" + locale;
        return cache.computeIfAbsent(cacheKey, k -> {
            Map<String, String> map = new LinkedHashMap<>();
            try {
                List<Map<String, Object>> rows = jdbc.queryForList(
                        "SELECT resource_type, resource_id, field, text FROM sys_i18n_text "
                                + "WHERE tenant_id = ? AND locale = ? AND status = 'ENABLED'",
                        tenant, locale);
                for (Map<String, Object> row : rows) {
                    String type = String.valueOf(row.get("resource_type"));
                    Object id = row.get("resource_id");
                    String field = String.valueOf(row.get("field"));
                    String text = row.get("text") == null ? null : String.valueOf(row.get("text"));
                    if (id != null && text != null && !text.isBlank()) {
                        map.put(key(type, ((Number) id).longValue(), field), text);
                    }
                }
            } catch (RuntimeException ignore) {
                // 表未初始化时不影响业务展示
            }
            return map;
        });
    }

    public String translate(String type, Long id, String field, String fallback) {
        if (id == null || fallback == null || fallback.isBlank()) {
            return fallback;
        }
        String text = all(LocaleContext.tag()).get(key(type, id, field));
        return text == null || text.isBlank() ? fallback : text;
    }

    /** 管理页：按资源类型列出（含未启用项）。 */
    public List<Map<String, Object>> list(String locale, String resourceType) {
        String tenant = TenantContext.tenantId();
        StringBuilder sql = new StringBuilder(
                "SELECT id, resource_type, resource_id, field, locale, text, status, updated_at "
                        + "FROM sys_i18n_text WHERE tenant_id = ? AND locale = ?");
        java.util.List<Object> args = new java.util.ArrayList<>();
        args.add(tenant);
        args.add(locale);
        if (resourceType != null && !resourceType.isBlank()) {
            sql.append(" AND resource_type = ?");
            args.add(resourceType);
        }
        sql.append(" ORDER BY resource_type, resource_id, field LIMIT 500");
        return jdbc.queryForList(sql.toString(), args.toArray());
    }

    /** 新增或覆盖一条翻译。 */
    public void upsert(String resourceType, Long resourceId, String field, String locale,
                       String text, String status) {
        if (resourceType == null || resourceType.isBlank() || resourceId == null
                || field == null || field.isBlank()) {
            throw new IllegalArgumentException("resourceType/resourceId/field required");
        }
        String tenant = TenantContext.tenantId();
        String loc = locale == null || locale.isBlank() ? LocaleContext.tag() : locale;
        String st = status == null || status.isBlank() ? "ENABLED" : status;
        String normalized = text == null ? "" : text.trim();
        Long id = jdbc.query(
                "SELECT id FROM sys_i18n_text WHERE tenant_id = ? AND resource_type = ? "
                        + "AND resource_id = ? AND field = ? AND locale = ? LIMIT 1",
                rs -> rs.next() ? rs.getLong(1) : null,
                tenant, resourceType, resourceId, field, loc);
        if (id == null) {
            jdbc.update("INSERT INTO sys_i18n_text (id, tenant_id, resource_type, resource_id, "
                            + "field, locale, text, status, updated_by, updated_at) "
                            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(3))",
                    com.baomidou.mybatisplus.core.toolkit.IdWorker.getId(),
                    tenant, resourceType, resourceId, field, loc, normalized, st,
                    TenantContext.userId());
        } else {
            jdbc.update("UPDATE sys_i18n_text SET text = ?, status = ?, updated_by = ?, "
                            + "updated_at = NOW(3) WHERE id = ?",
                    normalized, st, TenantContext.userId(), id);
        }
        cache.remove(tenant + "|" + loc);
    }
}
