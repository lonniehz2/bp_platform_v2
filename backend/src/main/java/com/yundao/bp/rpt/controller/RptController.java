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

    /** 发起导出：exportFormat=CSV（默认）或 EXCEL（.xls）。 */
    @PostMapping("/exports")
    public R<ExportTaskVO> export(@Valid @RequestBody ReportQueryCmd cmd,
                                  @RequestParam(required = false) Long userId) {
        return R.ok(reportService.export(cmd, userId));
    }

    /** 下载导出文件。CSV 与 Excel 分别给对应的 Content-Type。 */
    @GetMapping("/exports/{id}/download")
    public org.springframework.http.ResponseEntity<org.springframework.core.io.Resource> download(
            @PathVariable Long id) {
        String path = reportService.getTask(id).fileUrl();
        if (path == null || path.isBlank()) {
            return org.springframework.http.ResponseEntity.notFound().build();
        }
        java.io.File f = new java.io.File(path);
        if (!f.isFile()) {
            return org.springframework.http.ResponseEntity.notFound().build();
        }
        boolean excel = f.getName().toLowerCase().endsWith(".xls");
        String type = excel ? "application/vnd.ms-excel" : "text/csv;charset=UTF-8";
        String encoded;
        try {
            encoded = java.net.URLEncoder.encode(f.getName(),
                    java.nio.charset.StandardCharsets.UTF_8).replace("+", "%20");
        } catch (Exception e) {
            encoded = f.getName();
        }
        return org.springframework.http.ResponseEntity.ok()
                .header("Content-Type", type)
                .header("Content-Disposition",
                        "attachment; filename=\"" + f.getName() + "\"; filename*=UTF-8''" + encoded)
                .contentLength(f.length())
                .body(new org.springframework.core.io.FileSystemResource(f));
    }

    @GetMapping("/exports")
    public R<List<ExportTaskVO>> tasks(@RequestParam(required = false) Long userId) {
        return R.ok(reportService.listTasks(userId));
    }

    @GetMapping("/exports/{id}")
    public R<ExportTaskVO> task(@PathVariable Long id) {
        return R.ok(reportService.getTask(id));
    }

    /** 预览导出文件文本（CSV）。默认最多返回 20 万字符，可用 limit 调整。 */
    @GetMapping("/exports/{id}/content")
    public R<String> content(@PathVariable Long id,
                             @RequestParam(defaultValue = "200000") int limit) {
        String s = reportService.readFile(id);
        int cap = limit <= 0 ? s.length() : Math.min(limit, 5_000_000);
        return R.ok(s.length() > cap
                ? s.substring(0, cap) + "\n...(已截断，完整内容请查看服务器文件)"
                : s);
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
