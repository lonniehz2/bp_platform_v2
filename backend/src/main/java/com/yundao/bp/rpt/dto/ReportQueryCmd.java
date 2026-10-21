package com.yundao.bp.rpt.dto;

import jakarta.validation.constraints.NotBlank;
import java.time.LocalDate;

/**
 * 报表查询 / 导出请求。
 */
public record ReportQueryCmd(

        @NotBlank(message = "报表编码不能为空")
        String reportCode,

        LocalDate dateFrom,
        LocalDate dateTo,

        Long orgId,

        /** 页码（直接查询时使用） */
        Integer pageNum,
        Integer pageSize,

        /** 导出格式覆盖：CSV / EXCEL */
        String exportFormat
) {
}
