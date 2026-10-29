package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

/** 平台（租户）信息：编码不可修改，名称/类型/区域/状态可维护。 */
public record PlatformInfoVO(
        Long id,
        String tenantCode,
        String tenantName,
        String tenantType,
        String regionCode,
        String isolationMode,
        String status,
        LocalDateTime createTime
) {
    public static PlatformInfoVO from(com.yundao.bp.iam.entity.IamTenant t) {
        if (t == null) {
            return null;
        }
        return new PlatformInfoVO(t.getId(), t.getTenantCode(), t.getTenantName(),
                t.getTenantType(), t.getRegionCode(), t.getIsolationMode(), t.getStatus(),
                t.getCreateTime());
    }
}
