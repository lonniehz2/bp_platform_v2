# -*- coding: utf-8 -*-
"""生成 IoT 回调网关 + 设备指令模块的 Java 代码。"""
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


write('iot/gateway/entity/IotNonce.java', '''package com.yundao.bp.iot.gateway.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 回调 Nonce（防重放）。对应 {@code bp_iot_nonce}。 */
@Data
@TableName("bp_iot_nonce")
public class IotNonce {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String appId;
    private String nonce;
    private LocalDateTime expireAt;
    private LocalDateTime createTime;
}
''')

write('iot/gateway/entity/IotCallbackLog.java', '''package com.yundao.bp.iot.gateway.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 回调报文日志（含验签结果与处理状态）。对应 {@code bp_dev_callback_log}。 */
@Data
@TableName("bp_dev_callback_log")
public class IotCallbackLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String appId;
    private String msgType;
    private String eventId;
    private Integer signOk;
    private String rawBody;
    private String sourceIp;
    private Integer isDuplicate;
    private String processStatus;
    private String errorMsg;
    private LocalDateTime receiveTime;
    private LocalDateTime createTime;
}
''')

write('iot/gateway/mapper/IotNonceMapper.java', '''package com.yundao.bp.iot.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iot.gateway.entity.IotNonce;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface IotNonceMapper extends BaseMapper<IotNonce> {
}
''')

write('iot/gateway/mapper/IotCallbackLogMapper.java', '''package com.yundao.bp.iot.gateway.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iot.gateway.entity.IotCallbackLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface IotCallbackLogMapper extends BaseMapper<IotCallbackLog> {
}
''')

write('iot/gateway/IotSignatureVerifier.java', '''package com.yundao.bp.iot.gateway;

import com.yundao.bp.iot.config.IotSettings;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * IoT 回调验签。
 *
 * <pre>
 * canonical = method + "\\n" + path + "\\n" + appId + "\\n" + timestamp + "\\n" + nonce
 *           + "\\n" + sha256Hex(body)
 * signature = hex(HMAC-SHA256(appSecret, canonical))
 * </pre>
 */
@Component
public class IotSignatureVerifier {

    private static final Logger log = LoggerFactory.getLogger(IotSignatureVerifier.class);

    private final IotSettings settings;

    public IotSignatureVerifier(IotSettings settings) {
        this.settings = settings;
    }

    public boolean verify(String method, String path, String appId, String timestamp,
                          String nonce, String body, String signature) {
        if (appId == null || timestamp == null || nonce == null || signature == null) {
            return false;
        }
        String expectAppId = settings.getString("iot.callback.appId");
        if (expectAppId != null && !expectAppId.isBlank() && !expectAppId.equals(appId)) {
            log.warn("回调 appId 不匹配: {}", appId);
            return false;
        }
        long ts;
        try {
            ts = Long.parseLong(timestamp.trim());
        } catch (NumberFormatException e) {
            return false;
        }
        long tolerance = settings.timestampToleranceSeconds();
        if (Math.abs(System.currentTimeMillis() / 1000 - ts) > tolerance) {
            log.warn("回调时间戳超窗: {} 容忍 {}s", timestamp, tolerance);
            return false;
        }
        String secret = settings.getString("iot.callback.appSecret");
        if (secret == null || secret.isBlank()) {
            log.error("回调 appSecret 未配置，拒绝回调");
            return false;
        }
        String canonical = method.toUpperCase() + "\\n" + path + "\\n" + appId + "\\n"
                + timestamp + "\\n" + nonce + "\\n" + sha256Hex(body);
        String calc = hmacHex(secret, canonical);
        return calc != null && calc.equalsIgnoreCase(signature.trim());
    }

    public static String sha256Hex(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(md.digest(
                    (text == null ? "" : text).getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return "";
        }
    }

    private static String hmacHex(String secret, String canonical) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return HexFormat.of().formatHex(mac.doFinal(
                    canonical.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return null;
        }
    }
}
''')

write('dev/entity/DevCommand.java', '''package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 设备指令。对应 {@code bp_dev_command}。
 *
 * <p>平台不直连设备：指令经 IoT 平台下发，结果由回调 {@code command/ack} 回填。
 */
@Data
@TableName("bp_dev_command")
public class DevCommand {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String commandNo;

    /** LOCK_OPEN / DEVICE_REBOOT / DEVICE_SYNC_TIME / LOCK_MODE / ACCESS_OPEN / METER_SWITCH */
    private String commandType;

    private String deviceId;
    private String lockId;
    private String meterNo;

    /** 平台生成，回调按此关联 */
    private String requestId;

    private String paramsJson;

    /** PENDING / SENT / SUCCESS / FAILED / TIMEOUT / CANCELED */
    private String status;

    private Integer retryCount;
    private Integer maxRetry;
    private LocalDateTime timeoutAt;
    private LocalDateTime dispatchTime;
    private LocalDateTime ackTime;
    private String resultCode;
    private String resultMsg;
    private Integer costMs;

    private Long operatorId;
    private String operatorName;
    private String reason;
    /** CONSOLE / API / SCHEDULE */
    private String source;

    /** 拉合闸审批：PENDING / APPROVED / REJECTED（其他指令为空） */
    private String approveStatus;
    private Long approveBy;
    private LocalDateTime approveTime;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
''')

write('dev/mapper/DevCommandMapper.java', '''package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevCommand;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DevCommandMapper extends BaseMapper<DevCommand> {
}
''')

write('dev/iot/DeviceCommandClient.java', '''package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;

/**
 * 设备指令下发客户端抽象。平台不直连设备，实现走 IoT 平台。
 *
 * <p>配置 {@code bp.dev.command-mode=mock|real}。real 实现待 IoT 接口确认后接入。
 */
public interface DeviceCommandClient {

    CommandResult send(CommandRequest req);

    record CommandRequest(String requestId, String commandType, String lockId,
                          String meterNo, String paramsJson) {
    }

    record CommandResult(boolean success, String code, String message,
                         LocalDateTime deviceTime, Integer costMs) {
        public static CommandResult ok(String code, String message, Integer costMs) {
            return new CommandResult(true, code, message, LocalDateTime.now(), costMs);
        }

        public static CommandResult fail(String code, String message) {
            return new CommandResult(false, code, message, null, null);
        }
    }
}
''')

write('dev/iot/MockDeviceCommandClient.java', '''package com.yundao.bp.dev.iot;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟下发：直接返回成功，便于验证指令状态机与页面。 */
@Component
@ConditionalOnProperty(name = "bp.dev.command-mode", havingValue = "mock", matchIfMissing = true)
public class MockDeviceCommandClient implements DeviceCommandClient {

    private static final Logger log = LoggerFactory.getLogger(MockDeviceCommandClient.class);

    @Override
    public CommandResult send(CommandRequest req) {
        log.info("[mock] 下发指令 {} type={} lock={} meter={}", req.requestId(),
                req.commandType(), req.lockId(), req.meterNo());
        return CommandResult.ok("0", "mock ok", 12);
    }
}
''')

print('基础文件完成')
