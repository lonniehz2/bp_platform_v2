# -*- coding: utf-8 -*-
"""生成开放平台：5 张表实体 + Mapper + 服务 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(name, table, fields, doc, logic=False):
    lg = '\n    @TableLogic\n    private Integer isDeleted;\n' if logic else ''
    li = 'import com.baomidou.mybatisplus.annotation.TableLogic;\n' if logic else ''
    return f'''package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{li}import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
{lg}}}
'''


F['open/entity/OpenApp.java'] = ent('OpenApp', 'bp_open_app', [
    '    private String tenantId;',
    '    /** AppKey（公开展示，用于标识应用） */',
    '    private String appKey;',
    '    /** AppSecret（加密存储；仅在创建/重置时明文返回一次） */',
    '    private String appSecret;',
    '    private String appName;',
    '    /** THIRD_PARTY / INTERNAL / GOV */',
    '    private String appType;',
    '    private String ownerOrg;',
    '    private String contactName;',
    '    private String contactPhone;',
    '    /** IP 白名单（逗号分隔，为空表示不限制） */',
    '    private String ipWhitelist;',
    '    /** QPS 限流 */',
    '    private Integer qpsLimit;',
    '    /** 日调用配额（空=不限） */',
    '    private Integer dailyQuota;',
    '    /** 授权接口范围（逗号分隔，* 表示全部） */',
    '    private String scopeCodes;',
    '    private LocalDate expireDate;',
    '    /** ENABLED / DISABLED / EXPIRED */',
    '    private String appStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], '开放平台应用。对应 `bp_open_app`。', True)

F['open/entity/OpenApi.java'] = ent('OpenApi', 'bp_open_api', [
    '    private String apiCode;',
    '    private String apiName;',
    '    private String apiPath;',
    '    private String httpMethod;',
    '    /** HOUSE / PERSON / CONTRACT / ACCESS / ALERT / DEVICE */',
    '    private String apiGroup;',
    '    private Integer needAuth;',
    '    private Integer rateLimit;',
    '    private String apiStatus;',
    '    private String description;',
    '    private LocalDateTime createTime;',
], '开放接口清单。对应 `bp_open_api`。')

F['open/entity/OpenCallLog.java'] = ent('OpenCallLog', 'bp_open_call_log', [
    '    private String appKey;',
    '    private String apiCode;',
    '    private String apiPath;',
    '    private String requestId;',
    '    private String clientIp;',
    '    /** 请求体（已脱敏） */',
    '    private String requestBody;',
    '    private String responseCode;',
    '    private Integer successFlag;',
    '    private String errorMsg;',
    '    private Integer durationMs;',
    '    private LocalDateTime callTime;',
    '    private LocalDateTime createTime;',
], '开放接口调用日志。对应 `bp_open_call_log`（无 tenant_id，按 appKey 归属）。')

F['open/entity/OpenWebhook.java'] = ent('OpenWebhook', 'bp_open_webhook', [
    '    private String tenantId;',
    '    private String hookName;',
    '    private String callbackUrl;',
    '    /** 订阅事件（逗号分隔） */',
    '    private String eventTypes;',
    '    /** 签名密钥（HMAC-SHA256） */',
    '    private String secretKey;',
    '    private Integer retryTimes;',
    '    private Integer timeoutMs;',
    '    private String hookStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], 'Webhook 订阅。对应 `bp_open_webhook`。', True)

F['open/entity/OpenWebhookLog.java'] = ent('OpenWebhookLog', 'bp_open_webhook_log', [
    '    private String tenantId;',
    '    private Long hookId;',
    '    private String eventType;',
    '    private String eventId;',
    '    private String payload;',
    '    /** PENDING / SUCCESS / FAILED */',
    '    private String pushStatus;',
    '    private Integer retryCount;',
    '    private Integer httpStatus;',
    '    private String responseBody;',
    '    private LocalDateTime pushTime;',
    '    private LocalDateTime createTime;',
], 'Webhook 推送日志。对应 `bp_open_webhook_log`。')

for n in ('OpenApp', 'OpenApi', 'OpenCallLog', 'OpenWebhook', 'OpenWebhookLog'):
    F['open/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.open.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.open.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 签名工具 ====================
F['open/security/OpenSigner.java'] = '''package com.yundao.bp.open.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.stereotype.Component;

/**
 * 开放平台签名与密钥工具。
 *
 * <p><b>签名算法</b>（与主流开放平台一致，第三方易实现）：
 *
 * <pre>
 * 待签串 = METHOD + "\\n" + PATH + "\\n" + timestamp + "\\n" + nonce + "\\n" + body
 * sign   = Hex(HMAC-SHA256(appSecret, 待签串))
 * </pre>
 *
 * <p><b>为什么带 timestamp + nonce</b>：只签 body 可被重放；加时间戳限制窗口，
 * 加 nonce 保证一次性。二者缺一都能被重放攻击。
 */
@Component
public class OpenSigner {

    private static final SecureRandom RANDOM = new SecureRandom();

    /** 允许的时间偏差（毫秒）：5 分钟 */
    public static final long MAX_SKEW_MS = 5 * 60 * 1000L;

    /** 生成 AppSecret（32 字节 hex，仅创建时明文返回一次）。 */
    public String newSecret() {
        byte[] b = new byte[32];
        RANDOM.nextBytes(b);
        return HexFormat.of().formatHex(b);
    }

    /** 生成 AppKey（带前缀便于识别）。 */
    public String newAppKey() {
        byte[] b = new byte[12];
        RANDOM.nextBytes(b);
        return "AK" + HexFormat.of().formatHex(b).toUpperCase();
    }

    /** 生成 nonce。 */
    public String newNonce() {
        byte[] b = new byte[8];
        RANDOM.nextBytes(b);
        return HexFormat.of().formatHex(b);
    }

    /** 拼接待签串。 */
    public String buildPayload(String method, String path, String timestamp, String nonce,
                               String body) {
        return (method == null ? "" : method.toUpperCase()) + "\\n"
                + (path == null ? "" : path) + "\\n"
                + (timestamp == null ? "" : timestamp) + "\\n"
                + (nonce == null ? "" : nonce) + "\\n"
                + (body == null ? "" : body);
    }

    /** 计算签名（HMAC-SHA256 十六进制小写）。 */
    public String sign(String appSecret, String payload) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(appSecret.getBytes(StandardCharsets.UTF_8),
                    "HmacSHA256"));
            return HexFormat.of().formatHex(
                    mac.doFinal(payload.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("签名计算失败", e);
        }
    }

    /** 恒定时间比较（防时序攻击）。 */
    public boolean verify(String expect, String actual) {
        if (expect == null || actual == null) {
            return false;
        }
        return MessageDigest.isEqual(expect.getBytes(StandardCharsets.UTF_8),
                actual.getBytes(StandardCharsets.UTF_8));
    }

    /** 时间戳是否在允许窗口内。 */
    public boolean freshTimestamp(long timestampMs, long nowMs) {
        return Math.abs(nowMs - timestampMs) <= MAX_SKEW_MS;
    }

    /** IP 是否在白名单内（逗号分隔；空表示不限）。 */
    public boolean ipAllowed(String whitelist, String clientIp) {
        if (whitelist == null || whitelist.isBlank()) {
            return true;
        }
        for (String w : whitelist.split(",")) {
            String t = w.trim();
            if (t.isEmpty()) {
                continue;
            }
            if ("*".equals(t) || t.equals(clientIp)) {
                return true;
            }
            // 支持简单前缀网段：192.168.1.*
            if (t.endsWith("*") && clientIp != null
                    && clientIp.startsWith(t.substring(0, t.length() - 1))) {
                return true;
            }
        }
        return false;
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
