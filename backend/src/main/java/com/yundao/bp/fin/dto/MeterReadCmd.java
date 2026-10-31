package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public record MeterReadCmd(
        @NotNull(message = "读数不能为空") BigDecimal reading,
        LocalDateTime readTime,
        String source,
        String photoUrl,
        String remark
) {
}
