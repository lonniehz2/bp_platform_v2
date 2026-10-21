package com.yundao.bp.rpt.service;

import com.yundao.bp.rpt.dto.ExportTaskVO;
import com.yundao.bp.rpt.dto.ReportQueryCmd;
import com.yundao.bp.rpt.dto.ReportResultVO;
import com.yundao.bp.rpt.entity.RptReportDef;
import java.util.List;

/**
 * 报表服务：定义管理 + 查询执行 + 异步导出。
 */
public interface ReportService {

    /** 报表定义列表。 */
    List<RptReportDef> listReports(String reportType);

    /** 按定义查询数据（分页）。 */
    ReportResultVO query(ReportQueryCmd cmd);

    /** 创建并<b>同步执行</b>导出任务（生成 CSV 文件）。 */
    ExportTaskVO export(ReportQueryCmd cmd, Long userId);

    ExportTaskVO getTask(Long id);

    List<ExportTaskVO> listTasks(Long userId);

    /** 执行待处理任务（供定时任务/手动触发）。 */
    int runPendingTasks();

    /** 读取导出文件文本内容（供下载接口用）。 */
    String readFile(Long taskId);
}
