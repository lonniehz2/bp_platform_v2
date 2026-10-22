package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import java.time.LocalDate;

/**
 * 新建巡检计划。
 *
 * @param frequency DAY/WEEK/MONTH
 * @param nextRunDate 首次执行日（空则按今天）
 */
public record InspectionPlanCmd(
        String planName,
        Long orgId,
        Long spaceId,
        String inspectType,
        String frequency,
        LocalDate nextRunDate,
        Long assignUserId,
        String assignUserName,
        String remark) {
}
