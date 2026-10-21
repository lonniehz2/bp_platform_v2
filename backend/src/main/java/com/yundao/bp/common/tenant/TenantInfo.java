package com.yundao.bp.common.tenant;

import java.io.Serializable;
import java.util.List;

/**
 * 租户上下文信息（线程内传递）。
 *
 * @param tenantId    租户ID（必填）
 * @param userId      当前用户ID（可空：定时任务/回调场景）
 * @param orgId       当前组织ID（可空：表示可见范围为整个租户）
 * @param dataScope   数据范围：ALL 全部 / ORG 本组织及下级 / SELF 仅本人
 * @param orgIds      可见组织ID集合（dataScope=ORG 时使用）
 */
public record TenantInfo(String tenantId, Long userId, Long orgId,
                         String dataScope, List<Long> orgIds) implements Serializable {

    public static final String SCOPE_ALL = "ALL";
    public static final String SCOPE_ORG = "ORG";
    public static final String SCOPE_SELF = "SELF";

    /** 仅指定租户（系统任务 / MQ / IoT 回调使用）。 */
    public static TenantInfo of(String tenantId) {
        return new TenantInfo(tenantId, null, null, SCOPE_ALL, List.of());
    }

    public static TenantInfo of(String tenantId, Long userId) {
        return new TenantInfo(tenantId, userId, null, SCOPE_ALL, List.of());
    }

    public TenantInfo {
        if (tenantId == null || tenantId.isBlank()) {
            throw new IllegalArgumentException("tenantId 不能为空");
        }
        if (dataScope == null || dataScope.isBlank()) {
            dataScope = SCOPE_ALL;
        }
        if (orgIds == null) {
            orgIds = List.of();
        }
    }
}
