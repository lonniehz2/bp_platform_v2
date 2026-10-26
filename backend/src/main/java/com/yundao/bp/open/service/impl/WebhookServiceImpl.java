package com.yundao.bp.open.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.open.entity.OpenWebhook;
import com.yundao.bp.open.entity.OpenWebhookLog;
import com.yundao.bp.open.mapper.OpenWebhookLogMapper;
import com.yundao.bp.open.mapper.OpenWebhookMapper;
import com.yundao.bp.open.security.OpenSigner;
import com.yundao.bp.open.service.WebhookService;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Webhook 推送实现。
 *
 * <p>推送带上 {@code X-BP-Signature = HMAC-SHA256(secretKey, timestamp + "\n" + body)}，
 * 接收方据此验签，防止伪造回调。
 */
@Service
public class WebhookServiceImpl implements WebhookService {

    private static final Logger log = LoggerFactory.getLogger(WebhookServiceImpl.class);
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON =
            new com.fasterxml.jackson.databind.ObjectMapper()
                    .findAndRegisterModules();

    private final OpenWebhookMapper hookMapper;
    private final OpenWebhookLogMapper logMapper;
    private final OpenSigner signer;
    private final SnowflakeIdGenerator idGen;
    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5)).build();

    public WebhookServiceImpl(OpenWebhookMapper hookMapper, OpenWebhookLogMapper logMapper,
                              OpenSigner signer, SnowflakeIdGenerator idGen) {
        this.hookMapper = hookMapper;
        this.logMapper = logMapper;
        this.signer = signer;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpenWebhook subscribe(String hookName, String callbackUrl, String eventTypes,
                                 Integer retryTimes, Integer timeoutMs) {
        if (callbackUrl == null || !callbackUrl.startsWith("http")) {
            throw BizException.paramInvalid("回调地址必须是 http/https");
        }
        if (eventTypes == null || eventTypes.isBlank()) {
            throw BizException.paramInvalid("订阅事件不能为空");
        }
        OpenWebhook h = new OpenWebhook();
        h.setId(idGen.nextId());
        h.setTenantId(TenantContext.tenantId());
        h.setHookName(hookName);
        h.setCallbackUrl(callbackUrl);
        h.setEventTypes(eventTypes);
        h.setSecretKey(signer.newSecret());
        h.setRetryTimes(retryTimes == null ? 3 : retryTimes);
        h.setTimeoutMs(timeoutMs == null ? 5000 : timeoutMs);
        h.setHookStatus("ENABLED");
        h.setIsDeleted(0);
        h.setCreateTime(LocalDateTime.now());
        h.setUpdateTime(LocalDateTime.now());
        hookMapper.insert(h);
        log.info("Webhook 已订阅：{} → {}（事件 {}）", hookName, callbackUrl, eventTypes);
        return h;
    }

    @Override
    public List<OpenWebhook> list() {
        // 返回全部（含停用）：停用的订阅仍需在界面可见并可重新启用
        return hookMapper.selectList(new LambdaQueryWrapper<OpenWebhook>()
                .orderByDesc(OpenWebhook::getId));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpenWebhook setStatus(Long id, String status) {
        OpenWebhook h = hookMapper.selectById(id);
        if (h == null) {
            throw BizException.notFound("Webhook");
        }
        h.setHookStatus(status);
        h.setUpdateTime(LocalDateTime.now());
        hookMapper.updateById(h);
        return h;
    }

    @Override
    public int publish(String eventType, Map<String, Object> payload) {
        List<OpenWebhook> hooks = hookMapper.selectList(
                new LambdaQueryWrapper<OpenWebhook>()
                        .eq(OpenWebhook::getHookStatus, "ENABLED"));
        int ok = 0;
        for (OpenWebhook h : hooks) {
            if (!subscribed(h.getEventTypes(), eventType)) {
                continue;
            }
            String body;
            try {
                Map<String, Object> env = new LinkedHashMap<>();
                env.put("eventType", eventType);
                env.put("eventId", "EV" + idGen.nextId());
                env.put("timestamp", System.currentTimeMillis());
                env.put("data", payload);
                body = JSON.writeValueAsString(env);
            } catch (Exception e) {
                log.warn("Webhook 事件序列化失败：{}", e.getMessage());
                continue;
            }
            if (push(h, eventType, body)) {
                ok++;
            }
        }
        log.info("Webhook 事件发布：{} → 成功 {} 个订阅", eventType, ok);
        return ok;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int retryFailed(int limit) {
        List<OpenWebhookLog> logs = logMapper.selectList(
                new LambdaQueryWrapper<OpenWebhookLog>()
                        .eq(OpenWebhookLog::getPushStatus, "FAILED")
                        .orderByAsc(OpenWebhookLog::getId)
                        .last("LIMIT " + (limit <= 0 ? 20 : limit)));
        int n = 0;
        for (OpenWebhookLog l : logs) {
            OpenWebhook h = hookMapper.selectById(l.getHookId());
            if (h == null || !"ENABLED".equals(h.getHookStatus())) {
                continue;
            }
            l.setRetryCount((l.getRetryCount() == null ? 0 : l.getRetryCount()) + 1);
            boolean ok = doPost(h, l.getPayload(), l);
            l.setPushStatus(ok ? "SUCCESS" : "FAILED");
            l.setPushTime(LocalDateTime.now());
            logMapper.updateById(l);
            if (ok) {
                n++;
            }
        }
        return n;
    }

    @Override
    public PageResult<OpenWebhookLog> pageLogs(long pageNum, long pageSize, Long hookId,
                                               String pushStatus) {
        LambdaQueryWrapper<OpenWebhookLog> qw = new LambdaQueryWrapper<OpenWebhookLog>()
                .eq(hookId != null, OpenWebhookLog::getHookId, hookId)
                .eq(pushStatus != null && !pushStatus.isBlank(),
                        OpenWebhookLog::getPushStatus, pushStatus)
                .orderByDesc(OpenWebhookLog::getId);
        IPage<OpenWebhookLog> page = logMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    // ==================== 内部 ====================

    private boolean push(OpenWebhook h, String eventType, String body) {
        OpenWebhookLog l = new OpenWebhookLog();
        l.setId(idGen.nextId());
        l.setTenantId(h.getTenantId());
        l.setHookId(h.getId());
        l.setEventType(eventType);
        l.setEventId("EV" + l.getId());
        l.setPayload(body);
        l.setRetryCount(0);
        l.setPushTime(LocalDateTime.now());
        l.setCreateTime(LocalDateTime.now());
        boolean ok = doPost(h, body, l);
        l.setPushStatus(ok ? "SUCCESS" : "FAILED");
        logMapper.insert(l);
        if (!ok) {
            log.warn("Webhook 推送失败：{}（HTTP {}）", h.getCallbackUrl(), l.getHttpStatus());
        }
        return ok;
    }

    /**
     * 实际 HTTP 推送。
     *
     * <p>本地/内网无外网回调时必然失败，但<b>不影响主业务</b>：
     * 记录留痕，可由 {@code retryFailed} 补偿。
     */
    private boolean doPost(OpenWebhook h, String body, OpenWebhookLog l) {
        try {
            long ts = System.currentTimeMillis();
            String sig = signer.sign(h.getSecretKey(), ts + "\n" + body);
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(h.getCallbackUrl()))
                    .timeout(Duration.ofMillis(h.getTimeoutMs() == null ? 5000
                            : h.getTimeoutMs()))
                    .header("Content-Type", "application/json")
                    .header("X-BP-Event", l.getEventType() == null ? "" : l.getEventType())
                    .header("X-BP-Timestamp", String.valueOf(ts))
                    .header("X-BP-Signature", sig)
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            HttpResponse<String> resp = http.send(req,
                    HttpResponse.BodyHandlers.ofString());
            l.setHttpStatus(resp.statusCode());
            String rb = resp.body();
            l.setResponseBody(rb == null ? null
                    : (rb.length() > 1000 ? rb.substring(0, 1000) : rb));
            return resp.statusCode() >= 200 && resp.statusCode() < 300;
        } catch (Exception e) {
            l.setHttpStatus(null);
            l.setResponseBody("推送异常：" + e.getClass().getSimpleName()
                    + " " + e.getMessage());
            return false;
        }
    }

    private static boolean subscribed(String eventTypes, String eventType) {
        if (eventTypes == null || eventTypes.isBlank()) {
            return false;
        }
        if ("*".equals(eventTypes.trim())) {
            return true;
        }
        for (String e : eventTypes.split(",")) {
            String t = e.trim();
            // 支持前缀订阅：contract.* 匹配 contract.effective
            if (t.equals(eventType)) {
                return true;
            }
            if (t.endsWith(".*")
                    && eventType.startsWith(t.substring(0, t.length() - 1))) {
                return true;
            }
        }
        return false;
    }
}
