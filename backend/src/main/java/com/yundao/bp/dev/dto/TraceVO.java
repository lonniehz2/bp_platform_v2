package com.yundao.bp.dev.dto;

import java.time.LocalDate;
import java.util.List;

/**
 * 行为轨迹。
 */
public record TraceVO(
        String scope,
        Long targetId,
        LocalDate dateFrom,
        LocalDate dateTo,
        int totalRecords,
        int abnormalRecords,
        String summary,
        List<AccessVO> timeline
) {
}
