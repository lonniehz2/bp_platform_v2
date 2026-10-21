package com.yundao.bp.rpt.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.rpt.dto.ExportTaskVO;
import com.yundao.bp.rpt.dto.ReportQueryCmd;
import com.yundao.bp.rpt.dto.ReportResultVO;
import com.yundao.bp.rpt.entity.RptMetricDaily;
import com.yundao.bp.rpt.entity.RptReportDef;
import com.yundao.bp.rpt.entity.RptScreenDef;
import com.yundao.bp.rpt.service.MetricService;
import com.yundao.bp.rpt.service.ReportService;
import com.yundao.bp.rpt.service.ScreenService;
import com.yundao.bp.iam.security.RequirePerm;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 报表 / 大屏 / 指标接口（BC-06）。
 */
@RestController
@RequestMapping("/api/v1/rpt")
public class RptController {

    private final ReportService reportService;
    private final ScreenService screenService;
    private final MetricService metricService;

    public RptController(ReportService reportService, ScreenService screenService,
                         MetricService metricService) {
        this.reportService = reportService;
        this.screenService = screenService;
        this.metricService = metricService;
    }

    // ---------- 报表 ----------

    @GetMapping("/reports")
    public R<List<RptReportDef>> reports(@RequestParam(required = false) String reportType) {
        return R.ok(reportService.listReports(reportType));
    }

    /** 报表查询（在线预览）。 */
    @PostMapping("/reports/query")
    public R<ReportResultVO> query(@Valid @RequestBody ReportQueryCmd cmd) {
        return R.ok(reportService.query(cmd));
    }

    /** 发起导出（生成 CSV）。 */
    @PostMapping("/exports")
    public R<ExportTaskVO> export(@Valid @RequestBody ReportQueryCmd cmd,
                                  @RequestParam(required = false) Long userId) {
        return R.ok(reportService.export(cmd, userId));
    }

    @GetMapping("/exports")
    public R<List<ExportTaskVO>> tasks(@RequestParam(required = false) Long userId) {
        return R.ok(reportService.listTasks(userId));
    }

    @GetMapping("/exports/{id}")
    public R<ExportTaskVO> task(@PathVariable Long id) {
        return R.ok(reportService.getTask(id));
    }

    /** 预览导出文件文本（CSV 前 N 行）。 */
    @GetMapping("/exports/{id}/content")
    public R<String> content(@PathVariable Long id) {
        String s = reportService.readFile(id);
        return R.ok(s.length() > 4000 ? s.substring(0, 4000) + "...(截断)" : s);
    }

    @PostMapping("/exports/run-pending")
    public R<Integer> runPending() {
        return R.ok(reportService.runPendingTasks());
    }

    // ---------- 大屏 ----------

    @GetMapping("/screens")
    public R<List<RptScreenDef>> screens(@RequestParam(required = false) String screenType) {
        return R.ok(screenService.listScreens(screenType));
    }

    @GetMapping("/screens/{code}")
    public R<RptScreenDef> screen(@PathVariable String code) {
        return R.ok(screenService.getByCode(code));
    }

    /** ⭐ 大屏数据（配置驱动，逐组件取实时指标）。 */
    @GetMapping("/screens/{code}/data")
    public R<Map<String, Object>> screenData(@PathVariable String code,
                                             @RequestParam(required = false) Long orgId) {
        return R.ok(screenService.data(code, orgId));
    }

    @PostMapping("/screens")
    @RequirePerm("rpt:screen:edit")
    public R<RptScreenDef> saveScreen(@RequestBody ScreenCmd cmd) {
        return R.ok(screenService.save(cmd.screenCode(), cmd.screenName(), cmd.screenType(),
                cmd.layoutConfig(), cmd.widgetConfig(), cmd.refreshSeconds()));
    }

    // ---------- 指标 ----------

    /** 实时指标（驾驶舱/大屏通用）。 */
    @GetMapping("/metrics/current")
    public R<Map<String, Object>> current(@RequestParam(required = false) Long orgId) {
        return R.ok(metricService.currentAll(orgId));
    }

    @GetMapping("/metrics/current/{code}")
    public R<Double> currentOne(@PathVariable String code,
                                @RequestParam(required = false) Long orgId) {
        return R.ok(metricService.current(code, orgId));
    }

    /** 指标日快照（供趋势）。 */
    @PostMapping("/metrics/snapshot")
    public R<Integer> snapshot(@RequestParam(required = false) Long orgId) {
        return R.ok(metricService.snapshotToday(orgId));
    }

    @GetMapping("/metrics/trend/{code}")
    public R<List<RptMetricDaily>> trend(
            @PathVariable String code,
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(metricService.trend(code, orgId, dateFrom, dateTo));
    }

    public record ScreenCmd(String screenCode, String screenName, String screenType,
                            String layoutConfig, String widgetConfig,
                            Integer refreshSeconds) {
    }
}
