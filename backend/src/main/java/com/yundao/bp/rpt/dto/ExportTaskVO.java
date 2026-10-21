package com.yundao.bp.rpt.dto;

import com.yundao.bp.rpt.entity.RptExportTask;
import java.time.LocalDateTime;

/**
 * 导出任务视图。
 */
public record ExportTaskVO(
        Long id,
        String taskNo,
        String exportType,
        String reportCode,
        String fileName,
        String fileUrl,
        Long fileSize,
        Integer rowCount,
        String taskStatus,
        Integer progress,
        String failReason,
        LocalDateTime expireTime,
        LocalDateTime createTime,
        LocalDateTime finishTime
) {
    public static ExportTaskVO from(RptExportTask e) {
        if (e == null) {
            return null;
        }
        return new ExportTaskVO(e.getId(), e.getTaskNo(), e.getExportType(), e.getReportCode(),
                e.getFileName(), e.getFileUrl(), e.getFileSize(), e.getRowCount(),
                e.getTaskStatus(), e.getProgress(), e.getFailReason(), e.getExpireTime(),
                e.getCreateTime(), e.getFinishTime());
    }
}
