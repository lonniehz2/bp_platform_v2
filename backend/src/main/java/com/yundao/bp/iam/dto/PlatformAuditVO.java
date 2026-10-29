package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformAuditVO(
        Long id,
        String operatorName,
        String platformCode,
        String action,
        String detail,
        String ip,
        LocalDateTime createTime
) {
}
