package com.yundao.bp.open.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.open.dto.ApiCallCmd;
import com.yundao.bp.open.dto.AppCreateCmd;
import com.yundao.bp.open.dto.AppCreatedVO;
import com.yundao.bp.open.entity.OpenApi;
import com.yundao.bp.open.entity.OpenApp;
import com.yundao.bp.open.entity.OpenCallLog;
import com.yundao.bp.open.entity.OpenWebhook;
import com.yundao.bp.open.entity.OpenWebhookLog;
import com.yundao.bp.open.service.OpenPlatformService;
import com.yundao.bp.open.service.WebhookService;
import com.yundao.bp.sys.audit.Audit;
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
 * 开放平台接口（BC-08）。
 *
 * <p>面向第三方/政务系统：应用管理、接口清单、调用校验、调用日志、Webhook 订阅。
 */
@RestController
@RequestMapping("/api/v1/open")
public class OpenPlatformController {

    private final OpenPlatformService openService;
    private final WebhookService webhookService;

    public OpenPlatformController(OpenPlatformService openService,
                                  WebhookService webhookService) {
        this.openService = openService;
        this.webhookService = webhookService;
    }

    // ---------- 应用 ----------

    /** ⭐ 创建应用：返回的 appSecret 仅此一次可见。 */
    @PostMapping("/apps")
    @RequirePerm("open:app:manage")
    @Audit(type = "SECURITY", level = "CRITICAL", action = "创建开放平台应用")
    public R<AppCreatedVO> createApp(@Valid @RequestBody AppCreateCmd cmd) {
        return R.ok(openService.createApp(cmd, operator()));
    }

    /** ⭐ 重置密钥（旧密钥立即失效）。 */
    @PostMapping("/apps/{id}/reset-secret")
    @RequirePerm("open:app:manage")
    @Audit(type = "SECURITY", level = "CRITICAL", action = "重置开放平台密钥")
    public R<AppCreatedVO> resetSecret(@PathVariable Long id) {
        return R.ok(openService.resetSecret(id, operator()));
    }

    @PostMapping("/apps/{id}/status")
    @RequirePerm("open:app:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "变更开放应用状态")
    public R<OpenApp> setStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(openService.setStatus(id, cmd.status(), cmd.expireDate()));
    }

    @GetMapping("/apps")
    @RequirePerm("open:app:list")
    public R<List<OpenApp>> apps() {
        return R.ok(openService.listApps());
    }

    // ---------- 接口清单 ----------

    @GetMapping("/apis")
    public R<List<OpenApi>> apis(@RequestParam(required = false) String apiGroup) {
        return R.ok(openService.listApis(apiGroup));
    }

    // ---------- 调用校验 ----------

    /**
     * ⭐ 开放调用校验入口（网关用）。
     *
     * <p>校验签名/白名单/授权范围/时间窗，通过返回租户ID。
     * 无论成功失败都会落调用日志。
     */
    @com.yundao.bp.iam.security.RequirePerm("open:verify:verify")
    @PostMapping("/verify")
    public R<Map<String, Object>> verify(@Valid @RequestBody ApiCallCmd cmd,
                                         @RequestParam(required = false) String clientIp) {
        long t0 = System.currentTimeMillis();
        String ip = clientIp == null ? "unknown" : clientIp;
        try {
            String tenantId = openService.verify(cmd, ip);
            int ms = (int) (System.currentTimeMillis() - t0);
            openService.logCall(cmd.appKey(), cmd.apiCode(), "/open/" + cmd.apiCode(), ip,
                    cmd.body(), "BP00000", true, null, ms);
            return R.ok(Map.of("tenantId", tenantId, "apiCode", cmd.apiCode(),
                    "allowed", true));
        } catch (Exception e) {
            int ms = (int) (System.currentTimeMillis() - t0);
            String code = e instanceof com.yundao.bp.common.exception.BizException be
                    ? be.errorCode().name() : "BP99999";
            openService.logCall(cmd.appKey(), cmd.apiCode(), "/open/" + cmd.apiCode(), ip,
                    cmd.body(), code, false, e.getMessage(), ms);
            throw e;
        }
    }

    // ---------- 调用日志 ----------

    @GetMapping("/call-logs")
    @RequirePerm("open:log:list")
    public R<PageResult<OpenCallLog>> callLogs(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String appKey,
            @RequestParam(required = false) String apiCode,
            @RequestParam(required = false) Boolean successOnly,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(openService.pageCallLogs(pageNum, pageSize, appKey, apiCode, successOnly,
                dateFrom, dateTo));
    }

    @GetMapping("/usage")
    @RequirePerm("open:log:list")
    public R<Map<String, Object>> usage(
            @RequestParam(required = false) String appKey,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(openService.usage(appKey, dateFrom, dateTo));
    }

    // ---------- Webhook ----------

    @PostMapping("/webhooks")
    @RequirePerm("open:webhook:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "订阅 Webhook")
    public R<OpenWebhook> subscribe(@RequestBody HookCmd cmd) {
        return R.ok(webhookService.subscribe(cmd.hookName(), cmd.callbackUrl(),
                cmd.eventTypes(), cmd.retryTimes(), cmd.timeoutMs()));
    }

    @GetMapping("/webhooks")
    @RequirePerm("open:webhook:manage")
    public R<List<OpenWebhook>> hooks() {
        return R.ok(webhookService.list());
    }

    @PostMapping("/webhooks/{id}/status")
    @RequirePerm("open:webhook:manage")
    public R<OpenWebhook> hookStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(webhookService.setStatus(id, cmd.status()));
    }

    /** 发布业务事件（业务侧调用，也可由 MQ 消费触发）。 */
    @PostMapping("/webhooks/publish")
    public R<Integer> publish(@RequestBody PublishCmd cmd) {
        return R.ok(webhookService.publish(cmd.eventType(), cmd.payload()));
    }

    @GetMapping("/webhook-logs")
    @RequirePerm("open:webhook:manage")
    public R<PageResult<OpenWebhookLog>> hookLogs(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long hookId,
            @RequestParam(required = false) String pushStatus) {
        return R.ok(webhookService.pageLogs(pageNum, pageSize, hookId, pushStatus));
    }

    @PostMapping("/webhook-logs/retry")
    @RequirePerm("open:webhook:manage")
    public R<Integer> retryHook(@RequestParam(defaultValue = "20") int limit) {
        return R.ok(webhookService.retryFailed(limit));
    }

    private static String operator() {
        LoginUser u = LoginUser.get();
        return u == null ? "system" : (u.realName() == null ? u.username() : u.realName());
    }

    public record StatusCmd(String status, String expireDate) {
    }

    public record HookCmd(String hookName, String callbackUrl, String eventTypes,
                          Integer retryTimes, Integer timeoutMs) {
    }

    public record PublishCmd(String eventType, Map<String, Object> payload) {
    }
}
