# -*- coding: utf-8 -*-
"""离线判定 Job、拉闸执行 Job、联调工具接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


write('dev/job/DeviceOfflineJob.java', '''package com.yundao.bp.dev.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.mapper.DevEventMapper;
import com.yundao.bp.iot.config.IotSettings;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 离线判定：超过阈值无心跳的在线设备置离线，并生成 OFFLINE 事件。
 *
 * <p>阈值取系统参数 {@code iot.offline.thresholdSeconds}（默认 180 秒）。
 */
@Component
public class DeviceOfflineJob {

    private static final Logger log = LoggerFactory.getLogger(DeviceOfflineJob.class);

    private final DevDeviceMapper deviceMapper;
    private final DevEventMapper eventMapper;
    private final IotSettings settings;
    private final SnowflakeIdGenerator idGen;

    public DeviceOfflineJob(DevDeviceMapper deviceMapper, DevEventMapper eventMapper,
                            IotSettings settings, SnowflakeIdGenerator idGen) {
        this.deviceMapper = deviceMapper;
        this.eventMapper = eventMapper;
        this.settings = settings;
        this.idGen = idGen;
    }

    @Scheduled(initialDelay = 60_000, fixedDelay = 60_000)
    public void sweep() {
        int threshold = Math.max(30, settings.offlineThresholdSeconds());
        LocalDateTime deadline = LocalDateTime.now().minusSeconds(threshold);
        List<DevDevice> online = deviceMapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1));
        int n = 0;
        for (DevDevice d : online) {
            LocalDateTime last = d.getLastReportTime() != null
                    ? d.getLastReportTime() : d.getUpdateTime();
            if (last != null && last.isAfter(deadline)) {
                continue;
            }
            d.setOnlineStatus(0);
            d.setOfflineTime(LocalDateTime.now());
            d.setUpdateTime(LocalDateTime.now());
            deviceMapper.updateById(d);

            DevEvent e = new DevEvent();
            e.setId(idGen.nextId());
            e.setTenantId(d.getTenantId());
            e.setOrgId(d.getOrgId());
            e.setSpaceId(d.getSpaceId());
            e.setDeviceId(d.getDeviceId());
            e.setIdentifier("OFFLINE");
            e.setEventLevel("WARN");
            e.setEventTime(LocalDateTime.now());
            e.setBody("{\\"reason\\":\\"心跳超时 " + threshold + " 秒\\"}");
            e.setHandled(0);
            e.setIsDeleted(0);
            e.setCreateTime(LocalDateTime.now());
            e.setEventId("AUTO-OFF-" + d.getDeviceId() + "-"
                    + LocalDateTime.now().toLocalDate());
            try {
                // 同一设备同一天只产生一条自动离线事件
                Long dup = eventMapper.selectCount(new LambdaQueryWrapper<DevEvent>()
                        .eq(DevEvent::getEventId, e.getEventId()));
                if (dup == null || dup == 0) {
                    eventMapper.insert(e);
                }
            } catch (Exception ex) {
                log.debug("离线事件写入跳过: {}", ex.getMessage());
            }
            n++;
        }
        if (n > 0) {
            log.info("离线判定：{} 台设备置离线", n);
        }
    }
}
''')

write('dev/job/MeterSwitchExecuteJob.java', '''package com.yundao.bp.dev.job;

import com.yundao.bp.dev.service.impl.DevCommandServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 每 30 秒执行到点的拉合闸指令（审批通过且到达延迟执行时间）。 */
@Component
public class MeterSwitchExecuteJob {

    private static final Logger log = LoggerFactory.getLogger(MeterSwitchExecuteJob.class);

    private final DevCommandServiceImpl service;

    public MeterSwitchExecuteJob(DevCommandServiceImpl service) {
        this.service = service;
    }

    @Scheduled(initialDelay = 50_000, fixedDelay = 30_000)
    public void run() {
        try {
            int n = service.executeDueSwitches();
            if (n > 0) {
                log.info("拉合闸到点执行 {} 条", n);
            }
        } catch (Exception e) {
            log.warn("拉合闸执行失败: {}", e.getMessage());
        }
    }
}
''')

# 联调工具接口：回调日志 / 签名自测 / 重放
write('iot/gateway/IotToolController.java', '''package com.yundao.bp.iot.gateway;

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
        String canonical = "POST\\n" + path + "\\n" + appId + "\\n" + ts + "\\n" + nonce
                + "\\n" + bodyHash;
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
        String ts = String.valueOf(System.currentTimeMillis() / 1000);
        String nonce = "replay" + id + ts;
        String appId = settings.getString("iot.callback.appId");
        String secret = settings.getString("iot.callback.appSecret");
        String path = "/api/callback/iot/" + l.getMsgType();
        String body = l.getRawBody() == null ? "{}" : l.getRawBody();
        String signature = hmac(secret, "POST\\n" + path + "\\n" + appId + "\\n" + ts
                + "\\n" + nonce + "\\n" + IotSignatureVerifier.sha256Hex(body));
        IotCallbackService.Reply reply = callbackService.handle(l.getMsgType(), body,
                appId, ts, nonce, signature, "127.0.0.1", l.getTenantId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("httpStatus", reply.httpStatus());
        out.put("code", reply.code());
        out.put("message", reply.message());
        return R.ok(out);
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
''')

print('Job 与工具接口完成')
