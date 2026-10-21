# -*- coding: utf-8 -*-
"""生成报表/大屏控制器 + 种子数据"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

ctrl = '''package com.yundao.bp.rpt.controller;

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
'''
p = os.path.join(BASE, r'rpt\controller\RptController.java')
os.makedirs(os.path.dirname(p), exist_ok=True)
io.open(p, 'w', encoding='utf-8').write(ctrl)
print('  + rpt/controller/RptController.java')

# ---------- 种子数据 ----------
import pymysql  # noqa: E402

NOW = '2026-10-19 12:00:00'
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()

cur.execute("DELETE FROM bp_rpt_report_def WHERE tenant_id IS NULL")
REPORTS = [
    ('HOUSE_LEDGER', '房源台账', 'HOUSE'),
    ('CONTRACT_LEDGER', '合同台账', 'CONTRACT'),
    ('ARREARS_LEDGER', '欠费台账', 'FINANCE'),
]
for i, (code, name, typ) in enumerate(REPORTS, start=1):
    cur.execute("""INSERT INTO bp_rpt_report_def
        (id, tenant_id, report_code, report_name, report_type, export_format, report_status,
         is_deleted, create_time, update_time)
        VALUES (%s,NULL,%s,%s,%s,'CSV','ENABLED',0,%s,%s)""",
                (770000000000000000 + i * 100, code, name, typ, NOW, NOW))

cur.execute("DELETE FROM bp_rpt_screen_def WHERE tenant_id IS NULL")
WIDGETS = ('[{"code":"HOUSE_TOTAL","title":"房源总数","chart":"NUMBER"},'
           '{"code":"OCCUPANCY_RATE","title":"出租率(%)","chart":"GAUGE"},'
           '{"code":"HOUSE_VACANT","title":"空置房源","chart":"NUMBER"},'
           '{"code":"BILL_UNPAID_COUNT","title":"欠费账单","chart":"NUMBER"},'
           '{"code":"BILL_UNPAID_AMOUNT","title":"欠费金额(元)","chart":"NUMBER"},'
           '{"code":"PAYMENT_TOTAL_AMOUNT","title":"累计收款(元)","chart":"NUMBER"},'
           '{"code":"ACCESS_TODAY_COUNT","title":"今日开门","chart":"NUMBER"},'
           '{"code":"ACCESS_ABNORMAL_COUNT","title":"今日异常开门","chart":"LINE"}]')
cur.execute("""INSERT INTO bp_rpt_screen_def
    (id, tenant_id, screen_code, screen_name, screen_type, widget_config, refresh_seconds,
     screen_status, is_deleted, create_time, update_time)
    VALUES (%s,NULL,'OVERVIEW','住房保障运营总览','OVERVIEW',%s,60,'ENABLED',0,%s,%s)""",
            (780000000000000001, WIDGETS, NOW, NOW))

# 权限
cur.execute("DELETE FROM bp_iam_role_permission WHERE permission_id IN "
            "(SELECT id FROM bp_iam_permission WHERE perm_code='rpt:screen:edit')")
cur.execute("DELETE FROM bp_iam_permission WHERE perm_code='rpt:screen:edit'")
cur.execute("""INSERT INTO bp_iam_permission
    (id, parent_id, perm_code, perm_name, perm_type, sort_no, status, create_time)
    VALUES (790000000000000009,NULL,'rpt:screen:edit','大屏配置','API',300,'ENABLED',%s)""", (NOW,))
cur.execute("""INSERT INTO bp_iam_role_permission
    (id, tenant_id, role_id, permission_id, create_time)
    VALUES (796000000000000009,'350600',710000000000000001,790000000000000009,%s)""", (NOW,))

c.commit()
cur.execute("SELECT COUNT(*) FROM bp_rpt_report_def WHERE tenant_id IS NULL")
rp = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM bp_rpt_screen_def WHERE tenant_id IS NULL")
sc = cur.fetchone()[0]
print('报表定义 %d 条，大屏定义 %d 条' % (rp, sc))
c.close()
