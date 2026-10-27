package com.yundao.bp.iot.gateway;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iot.config.IotSettings;
import com.yundao.bp.iot.gateway.entity.IotCallbackLog;
import com.yundao.bp.iot.gateway.mapper.IotCallbackLogMapper;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** IoT 联调工具：回调日志查询、签名自测、回调重放。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotToolController {

    private final IotCallbackLogMapper logMapper;
    private final IotSignatureVerifier verifier;
    private final IotCallbackService callbackService;
    private final IotSettings settings;

    public IotToolController(IotCallbackLogMapper logMapper, IotSignatureVerifier verifier,
                             IotCallbackService callbackService, IotSettings settings) {
        this.logMapper = logMapper;
        this.verifier = verifier;
        this.callbackService = callbackService;
        this.settings = settings;
    }

    @RequirePerm("dev:command:view")
    @GetMapping("/callback-logs")
    public R<PageResult<IotCallbackLog>> logs(@RequestParam(defaultValue = "1") long pageNum,
                                              @RequestParam(defaultValue = "20") long pageSize,
                                              @RequestParam(required = false) String msgType,
                                              @RequestParam(required = false) String processStatus) {
        LambdaQueryWrapper<IotCallbackLog> qw = new LambdaQueryWrapper<IotCallbackLog>()
                .eq(msgType != null && !msgType.isBlank(), IotCallbackLog::getMsgType, msgType)
                .eq(processStatus != null && !processStatus.isBlank(),
                        IotCallbackLog::getProcessStatus, processStatus)
                .orderByDesc(IotCallbackLog::getReceiveTime);
        Page<IotCallbackLog> p = logMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(p.getTotal(), pageNum, pageSize, p.getRecords()));
    }

    /** 签名自测：返回 canonical 与 signature，便于与 IoT 方对照。 */
    @RequirePerm("dev:command:view")
    @PostMapping("/sign-preview")
    public R<Map<String, Object>> signPreview(@RequestBody SignCmd cmd) {
        String body = cmd.body() == null ? "{}" : cmd.body();
        String ts = cmd.timestamp() == null || cmd.timestamp().isBlank()
                ? String.valueOf(System.currentTimeMillis() / 1000) : cmd.timestamp();
        String nonce = cmd.nonce() == null || cmd.nonce().isBlank()
                ? "testnonce" : cmd.nonce();
        String appId = cmd.appId() == null || cmd.appId().isBlank()
                ? settings.getString("iot.callback.appId") : cmd.appId();
        String secret = cmd.appSecret() == null || cmd.appSecret().isBlank()
                ? settings.getString("iot.callback.appSecret") : cmd.appSecret();
        String path = "/api/callback/iot/" + (cmd.action() == null ? "event" : cmd.action());
        String bodyHash = IotSignatureVerifier.sha256Hex(body);
        String canonical = "POST\n" + path + "\n" + appId + "\n" + ts + "\n" + nonce
                + "\n" + bodyHash;
        String signature = hmac(secret, canonical);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("appId", appId);
        out.put("timestamp", ts);
        out.put("nonce", nonce);
        out.put("bodySha256", bodyHash);
        out.put("canonical", canonical);
        out.put("signature", signature);
        out.put("headerHint", "X-Iot-AppId / X-Iot-Timestamp / X-Iot-Nonce / X-Iot-Signature");
        return R.ok(out);
    }

    /** 重放一条历史回调（用当前配置密钥重新签名后交给处理器）。 */
    @RequirePerm("dev:command:retry")
    @PostMapping("/callback-logs/{id}/replay")
    public R<Map<String, Object>> replay(@PathVariable Long id) {
        IotCallbackLog l = logMapper.selectById(id);
        if (l == null) {
            throw new com.yundao.bp.common.exception.BizException(
                    com.yundao.bp.common.api.ErrorCode.NOT_FOUND, "回调日志不存在");
        }
        return R.ok(replayOne(l));
    }

    /**
     * 批量重放：断线补推 / 失败重试。
     *
     * @param from 接收时间起（yyyy-MM-dd HH:mm:ss）
     * @param to   接收时间止
     * @param status 处理状态，默认 FAILED；ALL 表示不限
     * @param limit 最多重放条数（≤200）
     */
    @RequirePerm("dev:command:retry")
    @PostMapping("/callback-logs/replay-range")
    public R<Map<String, Object>> replayRange(
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(defaultValue = "FAILED") String status,
            @RequestParam(defaultValue = "100") int limit) {
        java.time.LocalDateTime start = parseTime(from,
                java.time.LocalDateTime.now().minusDays(1));
        java.time.LocalDateTime end = parseTime(to, java.time.LocalDateTime.now());
        int cap = Math.max(1, Math.min(limit, 200));
        LambdaQueryWrapper<IotCallbackLog> qw = new LambdaQueryWrapper<IotCallbackLog>()
                .ge(IotCallbackLog::getReceiveTime, start)
                .le(IotCallbackLog::getReceiveTime, end)
                .eq(!"ALL".equalsIgnoreCase(status) && status != null && !status.isBlank(),
                        IotCallbackLog::getProcessStatus, status)
                .orderByAsc(IotCallbackLog::getReceiveTime)
                .last("LIMIT " + cap);
        java.util.List<IotCallbackLog> logs = logMapper.selectList(qw);
        int success = 0;
        int failed = 0;
        java.util.List<Map<String, Object>> details = new java.util.ArrayList<>();
        for (IotCallbackLog l : logs) {
            Map<String, Object> one = replayOne(l);
            one.put("id", l.getId());
            one.put("msgType", l.getMsgType());
            boolean ok = one.get("httpStatus") instanceof Integer code && code == 200;
            if (ok) {
                success++;
            } else {
                failed++;
            }
            if (details.size() < 20) {
                details.add(one);
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("from", start.toString());
        out.put("to", end.toString());
        out.put("status", status);
        out.put("matched", logs.size());
        out.put("success", success);
        out.put("failed", failed);
        out.put("details", details);
        return R.ok(out);
    }

    private Map<String, Object> replayOne(IotCallbackLog l) {
        String ts = String.valueOf(System.currentTimeMillis() / 1000);
        String nonce = "replay" + l.getId() + ts;
        String appId = settings.getString("iot.callback.appId");
        String secret = settings.getString("iot.callback.appSecret");
        String path = "/api/callback/iot/" + l.getMsgType();
        String body = l.getRawBody() == null ? "{}" : l.getRawBody();
        String signature = hmac(secret, "POST\n" + path + "\n" + appId + "\n" + ts
                + "\n" + nonce + "\n" + IotSignatureVerifier.sha256Hex(body));
        IotCallbackService.Reply reply = callbackService.handle(l.getMsgType(), body,
                appId, ts, nonce, signature, "127.0.0.1", l.getTenantId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("httpStatus", reply.httpStatus());
        out.put("code", reply.code());
        out.put("message", reply.message());
        return out;
    }

    private static java.time.LocalDateTime parseTime(String text,
                                                     java.time.LocalDateTime fallback) {
        if (text == null || text.isBlank()) {
            return fallback;
        }
        try {
            return java.time.LocalDateTime.parse(text.trim().replace(' ', 'T'));
        } catch (Exception e) {
            return fallback;
        }
    }

    private static String hmac(String secret, String canonical) {
        try {
            javax.crypto.Mac mac = javax.crypto.Mac.getInstance("HmacSHA256");
            mac.init(new javax.crypto.spec.SecretKeySpec(
                    secret.getBytes(java.nio.charset.StandardCharsets.UTF_8), "HmacSHA256"));
            return java.util.HexFormat.of().formatHex(mac.doFinal(
                    canonical.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return null;
        }
    }

    public record SignCmd(String action, String appId, String appSecret, String timestamp,
                          String nonce, String body) {
    }
}
