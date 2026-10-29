package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformVO(
        Long id,
        String tenantCode,
        String tenantName,
        String tenantType,
        String regionCode,
        String status,
        String contactName,
        String contactPhone,
        String businessTypeCode,
        Long adminCount,
        LocalDateTime createTime,
        LocalDateTime archiveTime
) {
}
