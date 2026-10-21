package com.yundao.bp.gov.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.gov.entity.GovAdapterConfig;
import com.yundao.bp.gov.entity.GovReportDetail;
import com.yundao.bp.gov.entity.GovReportTask;
import com.yundao.bp.gov.service.GovReportService;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
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
 * 监管报送接口（BC-08）。
 *
 * <p>面向房管局/公安/住建：适配器配置、报送任务、报送明细、失败补报。
 */
@RestController
@RequestMapping("/api/v1/gov")
public class GovReportController {

    private final GovReportService service;

    public GovReportController(GovReportService service) {
        this.service = service;
    }

    // ---------- 适配器 ----------

    @GetMapping("/adapters")
    @RequirePerm("gov:adapter:manage")
    public R<List<GovAdapterConfig>> adapters() {
        return R.ok(service.listAdapters());
    }

    @PostMapping("/adapters")
    @RequirePerm("gov:adapter:manage")
    @Audit(type = "CONFIG", level = "CRITICAL", action = "配置政务适配器")
    public R<GovAdapterConfig> saveAdapter(@RequestBody AdapterCmd cmd) {
        return R.ok(service.saveAdapter(cmd.adapterCode(), cmd.adapterName(),
                cmd.systemType(), cmd.protocol(), cmd.endpoint(), cmd.authType(),
                cmd.degradeMode()));
    }

    // ---------- 报送 ----------

    /** ⭐ 发起报送（生成任务 + 明细 + 适配器日志）。 */
    @PostMapping("/reports")
    @RequirePerm("gov:report:submit")
    @Audit(type = "DATA", level = "IMPORTANT", action = "发起监管报送")
    public R<GovReportTask> submit(@RequestBody ReportCmd cmd) {
        return R.ok(service.submit(cmd.targetSystem(), cmd.reportType(), cmd.dateFrom(),
                cmd.dateTo(), operator()));
    }

    @GetMapping("/reports")
    @RequirePerm("gov:report:list")
    public R<PageResult<GovReportTask>> tasks(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String targetSystem,
            @RequestParam(required = false) String reportType,
            @RequestParam(required = false) String taskStatus) {
        return R.ok(service.pageTasks(pageNum, pageSize, targetSystem, reportType,
                taskStatus));
    }

    @GetMapping("/reports/{id}")
    @RequirePerm("gov:report:list")
    public R<GovReportTask> task(@PathVariable Long id) {
        return R.ok(service.getTask(id));
    }

    /** 报送明细（含每条请求快照与外部 ID）。 */
    @GetMapping("/reports/{id}/details")
    @RequirePerm("gov:report:list")
    public R<List<GovReportDetail>> details(@PathVariable Long id) {
        return R.ok(service.taskDetails(id));
    }

    /** ⭐ 失败补报（部分成功后精确补报）。 */
    @PostMapping("/reports/{id}/retry")
    @RequirePerm("gov:report:submit")
    @Audit(type = "DATA", level = "IMPORTANT", action = "监管报送失败补报")
    public R<Integer> retry(@PathVariable Long id) {
        return R.ok(service.retryFailed(id));
    }

    @GetMapping("/stats")
    @RequirePerm("gov:report:list")
    public R<Map<String, Object>> stats(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.stats(dateFrom, dateTo));
    }

    private static String operator() {
        LoginUser u = LoginUser.get();
        return u == null ? "system" : (u.realName() == null ? u.username() : u.realName());
    }

    public record AdapterCmd(String adapterCode, String adapterName, String systemType,
                             String protocol, String endpoint, String authType,
                             String degradeMode) {
    }

    public record ReportCmd(String targetSystem, String reportType,
                            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateFrom,
                            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateTo) {
    }
}
