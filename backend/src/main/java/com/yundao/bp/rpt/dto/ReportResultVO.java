package com.yundao.bp.rpt.dto;

import java.util.List;
import java.util.Map;

/**
 * 报表查询结果。
 *
 * @param columns 列定义（key + title）
 * @param rows    数据行
 */
public record ReportResultVO(
        String reportCode,
        String reportName,
        List<Map<String, String>> columns,
        List<Map<String, Object>> rows,
        long total,
        String summary
) {
}
