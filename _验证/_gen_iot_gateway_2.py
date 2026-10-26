# -*- coding: utf-8 -*-
"""生成回调服务、控制器、指令服务与超时 Job。"""
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


# ---------------- 回调服务 ----------------
write('iot/gateway/IotCallbackService.java', '''package com.yundao.bp.iot.gateway;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.dev.entity.DevAccessRecord;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.dev.mapper.DevAccessRecordMapper;
import com.yundao.bp.dev.mapper.DevCommandMapper;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.mapper.DevEventMapper;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.iot.config.IotSettings;
import com.yundao.bp.iot.gateway.entity.IotCallbackLog;
import com.yundao.bp.iot.gateway.entity.IotNonce;
import com.yundao.bp.iot.gateway.mapper.IotCallbackLogMapper;
import com.yundao.bp.iot.gateway.mapper.IotNonceMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * IoT 回调处理：验签 → 防重放 → 幂等 → 分发到业务处理。
 *
 * <p>响应约定：验签失败 401；重放/重复 200 + SUCCESS（避免 IoT 无意义重试）；
 * 处理异常 500（让 IoT 重试）。
 */
@Service
public class IotCallbackService {

    private static final Logger log = LoggerFactory.getLogger(IotCallbackService.class);
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final IotSignatureVerifier verifier;
    private final IotSettings settings;
    private final IotNonceMapper nonceMapper;
    private final IotCallbackLogMapper logMapper;
    private final SnowflakeIdGenerator idGen;
    private final ObjectMapper json = new ObjectMapper();

    private final DevEventMapper eventMapper;
    private final DevAccessRecordMapper accessMapper;
    private final DevDeviceMapper deviceMapper;
    private final DevCommandMapper commandMapper;
    private final GrantTaskMapper grantTaskMapper;
    private final FinMeterReadingMapper meterMapper;
    private final AssetHouseMapper houseMapper;

    public IotCallbackService(IotSignatureVerifier verifier, IotSettings settings,
                              IotNonceMapper nonceMapper, IotCallbackLogMapper logMapper,
                              SnowflakeIdGenerator idGen, DevEventMapper eventMapper,
                              DevAccessRecordMapper accessMapper, DevDeviceMapper deviceMapper,
                              DevCommandMapper commandMapper, GrantTaskMapper grantTaskMapper,
                              FinMeterReadingMapper meterMapper, AssetHouseMapper houseMapper) {
        this.verifier = verifier;
        this.settings = settings;
        this.nonceMapper = nonceMapper;
        this.logMapper = logMapper;
        this.idGen = idGen;
        this.eventMapper = eventMapper;
        this.accessMapper = accessMapper;
        this.deviceMapper = deviceMapper;
        this.commandMapper = commandMapper;
        this.grantTaskMapper = grantTaskMapper;
        this.meterMapper = meterMapper;
        this.houseMapper = houseMapper;
    }

    /** 处理一次回调；返回 null 表示成功，否则返回错误码 + HTTP 状态。 */
    public Reply handle(String action, String body, String appId, String timestamp,
                        String nonce, String signature, String sourceIp, String tenantHeader) {
        String path = "/api/callback/iot/" + action;
        String tenantId = (tenantHeader == null || tenantHeader.isBlank())
                ? settings.getString("iot.callback.defaultTenant") : tenantHeader.trim();
        if (tenantId == null || tenantId.isBlank()) {
            tenantId = "350600";
        }
        boolean verifyOn = !"false".equalsIgnoreCase(settings.getString("iot.callback.verify"));
        boolean signOk = !verifyOn || verifier.verify("POST", path, appId, timestamp, nonce, body, signature);
        if (!signOk) {
            saveLog(tenantId, action, appId, null, 0, body, sourceIp, "REJECTED", "验签失败", 0);
            return new Reply(401, "SIGNATURE_INVALID", "signature invalid");
        }

        TenantContext.set(TenantInfo.of(tenantId, null));
        try {
            if (nonce != null && !nonce.isBlank()) {
                if (!saveNonce(tenantId, appId, nonce)) {
                    saveLog(tenantId, action, appId, null, 1, body, sourceIp, "DUPLICATE",
                            "nonce 重复", 1);
                    return new Reply(200, "SUCCESS", "duplicate");
                }
            }
            JsonNode node = json.readTree(body.isBlank() ? "{}" : body);
            String eventId = text(node, "eventId");
            IotCallbackLog cl = saveLog(tenantId, action, appId, eventId, 1, body, sourceIp,
                    "RECEIVED", null, 0);
            if (cl == null) {
                return new Reply(200, "SUCCESS", "duplicate");
            }
            try {
                dispatch(action, node, tenantId);
                updateLog(cl, "DONE", null);
                return new Reply(200, "SUCCESS", "ok");
            } catch (Exception e) {
                log.error("回调处理失败 action={} err={}", action, e.getMessage(), e);
                updateLog(cl, "FAILED", trim(e.getMessage(), 480));
                return new Reply(500, "SERVER_ERROR", trim(e.getMessage(), 200));
            }
        } catch (Exception e) {
            log.error("回调解析失败 action={}", action, e);
            return new Reply(400, "PARAM_INVALID", trim(e.getMessage(), 200));
        } finally {
            TenantContext.clear();
        }
    }

    private void dispatch(String action, JsonNode node, String tenantId) throws Exception {
        switch (action) {
            case "event" -> onEvent(node, tenantId);
            case "access" -> onAccess(node, tenantId);
            case "command/ack", "command-ack" -> onCommandAck(node, tenantId);
            case "grant/ack", "grant-ack" -> onGrantAck(node, tenantId);
            case "heartbeat" -> onHeartbeat(node, tenantId);
            case "meter" -> onMeter(node, tenantId);
            case "device-status" -> onDeviceStatus(node, tenantId);
            case "alarm-ack" -> onAlarmAck(node, tenantId);
            default -> throw new IllegalArgumentException("未知回调动作: " + action);
        }
    }

    // ---------- 业务处理 ----------

    private void onEvent(JsonNode n, String tenantId) {
        DevEvent e = new DevEvent();
        e.setId(idGen.nextId());
        e.setTenantId(tenantId);
        e.setEventId(text(n, "eventId"));
        e.setDeviceId(text(n, "deviceId") != null ? text(n, "deviceId") : text(n, "lockId"));
        e.setIdentifier(text(n, "identifier"));
        e.setEventLevel(text(n, "eventLevel") == null ? "INFO" : text(n, "eventLevel"));
        e.setEventTime(parseTime(text(n, "eventTime")));
        JsonNode body = n.get("body");
        e.setBody(body == null ? null : (body.isTextual() ? body.asText() : body.toString()));
        e.setHandled(0);
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        fillDeviceScope(e, e.getDeviceId());
        try {
            eventMapper.insert(e);
        } catch (DuplicateKeyException dup) {
            log.info("设备事件重复: {}", e.getEventId());
        }
    }

    private void onAccess(JsonNode n, String tenantId) {
        List<JsonNode> items = new ArrayList<>();
        if (n.isArray()) {
            n.forEach(items::add);
        } else {
            items.add(n);
        }
        for (JsonNode x : items) {
            DevAccessRecord r = new DevAccessRecord();
            r.setId(idGen.nextId());
            r.setTenantId(tenantId);
            r.setEventId(text(x, "eventId"));
            r.setDeviceId(text(x, "deviceId"));
            r.setLockId(text(x, "lockId"));
            r.setOpenType(text(x, "openType") == null ? "OTHER" : text(x, "openType"));
            r.setOpenTime(parseTime(text(x, "openTime")));
            r.setPersonId(longVal(x, "personId"));
            r.setTargetUserMobile(text(x, "targetUserMobile"));
            r.setIsTrusted(intVal(x, "isTrusted", 1));
            r.setSource("IOT");
            r.setCreateTime(LocalDateTime.now());
            DevDevice d = findDevice(text(x, "deviceId"), text(x, "lockId"));
            if (d != null) {
                r.setSpaceId(d.getSpaceId());
                r.setOrgId(d.getOrgId());
                r.setHouseId(findHouseId(d.getSpaceId()));
            }
            try {
                accessMapper.insert(r);
            } catch (DuplicateKeyException dup) {
                log.info("开门记录重复: {}", r.getEventId());
            }
        }
    }

    private void onCommandAck(JsonNode n, String tenantId) {
        String requestId = text(n, "requestId");
        if (requestId == null) {
            throw new IllegalArgumentException("requestId 不能为空");
        }
        DevCommand c = commandMapper.selectOne(new LambdaQueryWrapper<DevCommand>()
                .eq(DevCommand::getRequestId, requestId).last("LIMIT 1"));
        if (c == null) {
            throw new IllegalArgumentException("指令不存在: " + requestId);
        }
        String code = text(n, "code");
        boolean ok = "0".equals(code) || "SUCCESS".equalsIgnoreCase(code);
        c.setStatus(ok ? "SUCCESS" : "FAILED");
        c.setResultCode(code);
        c.setResultMsg(trim(text(n, "message"), 480));
        c.setAckTime(LocalDateTime.now());
        c.setCostMs(intVal(n, "costMs", null));
        c.setUpdateTime(LocalDateTime.now());
        commandMapper.updateById(c);
    }

    private void onGrantAck(JsonNode n, String tenantId) {
        String serviceId = text(n, "serviceId");
        if (serviceId == null) {
            throw new IllegalArgumentException("serviceId 不能为空");
        }
        GrantTask t = grantTaskMapper.selectOne(new LambdaQueryWrapper<GrantTask>()
                .eq(GrantTask::getServiceId, serviceId).last("LIMIT 1"));
        if (t == null) {
            throw new IllegalArgumentException("授权任务不存在: " + serviceId);
        }
        boolean success = n.path("success").asBoolean(false);
        int failCount = intVal(n, "failCount", 0);
        int total = t.getLockCount() == null ? failCount : t.getLockCount();
        t.setTaskStatus(!success ? "FAILED" : (failCount > 0 ? "PARTIAL" : "SUCCESS"));
        t.setSuccessCount(Math.max(0, total - failCount));
        t.setFailCount(failCount);
        t.setCallbackTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        grantTaskMapper.updateById(t);
    }

    private void onHeartbeat(JsonNode n, String tenantId) {
        List<JsonNode> items = new ArrayList<>();
        if (n.isArray()) {
            n.forEach(items::add);
        } else {
            items.add(n);
        }
        LocalDateTime now = LocalDateTime.now();
        for (JsonNode x : items) {
            DevDevice d = findDevice(text(x, "deviceId"), text(x, "lockId"));
            if (d == null) {
                continue;
            }
            boolean online = x.path("online").asBoolean(true);
            d.setOnlineStatus(online ? 1 : 0);
            if (online) {
                d.setOnlineTime(now);
            } else {
                d.setOfflineTime(now);
            }
            Integer battery = intVal(x, "battery", null);
            if (battery != null) {
                d.setBattery(battery);
            }
            String rssi = text(x, "rssi");
            if (rssi != null) {
                d.setRssi(rssi);
            }
            d.setLastReportTime(parseTime(text(x, "reportTime")) == null
                    ? now : parseTime(text(x, "reportTime")));
            d.setUpdateTime(now);
            deviceMapper.updateById(d);
        }
    }

    private void onMeter(JsonNode n, String tenantId) {
        List<JsonNode> items = new ArrayList<>();
        if (n.isArray()) {
            n.forEach(items::add);
        } else {
            items.add(n);
        }
        for (JsonNode x : items) {
            String meterNo = text(x, "meterNo");
            String deviceId = text(x, "deviceId");
            DevDevice d = findDevice(deviceId, null);
            if (d == null && meterNo != null) {
                d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                        .eq(DevDevice::getDeviceId, meterNo).last("LIMIT 1"));
            }
            Long houseId = d == null ? null : findHouseId(d.getSpaceId());
            String meterType = text(x, "meterType");
            Long feeItemId = houseId == null ? null : findFeeItemId(meterType);
            if (houseId == null || feeItemId == null) {
                log.warn("表计读数未入库（缺房源或收费项目） meter={} type={} device={}",
                        meterNo, meterType, deviceId);
                continue;
            }
            BigDecimal reading = x.path("reading").decimalValue();
            LocalDate readDate = parseTime(text(x, "readTime")) == null
                    ? LocalDate.now() : parseTime(text(x, "readTime")).toLocalDate();
            FinMeterReading prev = meterMapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                    .eq(FinMeterReading::getHouseId, houseId)
                    .eq(FinMeterReading::getFeeItemId, feeItemId)
                    .orderByDesc(FinMeterReading::getReadDate).last("LIMIT 1"));
            BigDecimal prevReading = prev == null ? BigDecimal.ZERO : prev.getReading();
            BigDecimal usage = reading.subtract(prevReading);
            if (usage.compareTo(BigDecimal.ZERO) < 0) {
                usage = BigDecimal.ZERO;
            }
            FinMeterReading e = new FinMeterReading();
            e.setId(idGen.nextId());
            e.setTenantId(tenantId);
            e.setOrgId(d.getOrgId());
            e.setHouseId(houseId);
            e.setFeeItemId(feeItemId);
            e.setDeviceId(meterNo != null ? meterNo : deviceId);
            e.setReadDate(readDate);
            e.setReading(reading);
            e.setPrevReading(prevReading);
            e.setUsageAmount(usage);
            e.setUnitPrice(BigDecimal.ZERO);
            e.setAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
            e.setBillStatus("UNBILLED");
            e.setRemark("IoT 上报 " + (text(x, "source") == null ? "PUSH" : text(x, "source")));
            e.setIsDeleted(0);
            e.setCreateTime(LocalDateTime.now());
            meterMapper.insert(e);
        }
    }

    private void onDeviceStatus(JsonNode n, String tenantId) {
        DevDevice d = findDevice(text(n, "deviceId"), text(n, "lockId"));
        if (d == null) {
            throw new IllegalArgumentException("设备不存在: " + text(n, "deviceId"));
        }
        String status = text(n, "status");
        boolean online = "ONLINE".equalsIgnoreCase(status);
        LocalDateTime time = parseTime(text(n, "time")) == null
                ? LocalDateTime.now() : parseTime(text(n, "time"));
        d.setOnlineStatus(online ? 1 : 0);
        if (online) {
            d.setOnlineTime(time);
        } else {
            d.setOfflineTime(time);
        }
        d.setLastReportTime(time);
        d.setUpdateTime(LocalDateTime.now());
        deviceMapper.updateById(d);

        DevEvent e = new DevEvent();
        e.setId(idGen.nextId());
        e.setTenantId(tenantId);
        e.setEventId("DS-" + d.getDeviceId() + "-" + time);
        e.setDeviceId(d.getDeviceId());
        e.setIdentifier(online ? "ONLINE" : "OFFLINE");
        e.setEventLevel("INFO");
        e.setEventTime(time);
        e.setBody("{\\"reason\\":\\"" + (text(n, "reason") == null ? "UNKNOWN" : text(n, "reason")) + "\\"}");
        e.setHandled(0);
        e.setIsDeleted(0);
        e.setOrgId(d.getOrgId());
        e.setSpaceId(d.getSpaceId());
        e.setCreateTime(LocalDateTime.now());
        try {
            eventMapper.insert(e);
        } catch (DuplicateKeyException ignored) {
        }
    }

    private void onAlarmAck(JsonNode n, String tenantId) {
        String eventId = text(n, "eventId");
        if (eventId == null) {
            throw new IllegalArgumentException("eventId 不能为空");
        }
        DevEvent e = eventMapper.selectOne(new LambdaQueryWrapper<DevEvent>()
                .eq(DevEvent::getEventId, eventId).last("LIMIT 1"));
        if (e == null) {
            throw new IllegalArgumentException("事件不存在: " + eventId);
        }
        e.setHandled(1);
        e.setHandleRemark("IoT 告警恢复 " + (text(n, "recoverTime") == null ? "" : text(n, "recoverTime")));
        e.setHandleTime(LocalDateTime.now());
        e.setHandleBy("iot");
        eventMapper.updateById(e);
    }

    // ---------- 工具 ----------

    private DevEvent fillDeviceScope(DevEvent e, String deviceId) {
        DevDevice d = findDevice(deviceId, null);
        if (d != null) {
            e.setOrgId(d.getOrgId());
            e.setSpaceId(d.getSpaceId());
        }
        return e;
    }

    private DevDevice findDevice(String deviceId, String lockId) {
        if (deviceId != null && !deviceId.isBlank()) {
            DevDevice d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, deviceId).last("LIMIT 1"));
            if (d != null) {
                return d;
            }
        }
        if (lockId != null && !lockId.isBlank()) {
            return deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, lockId).last("LIMIT 1"));
        }
        return null;
    }

    private Long findHouseId(Long spaceId) {
        if (spaceId == null) {
            return null;
        }
        AssetHouse h = houseMapper.selectOne(new LambdaQueryWrapper<AssetHouse>()
                .eq(AssetHouse::getSpaceId, spaceId).last("LIMIT 1"));
        return h == null ? null : h.getId();
    }

    private Long findFeeItemId(String meterType) {
        if (meterType == null) {
            return null;
        }
        // ELEC / WATER / GAS / HEAT → 收费项目编码前缀约定
        return null;
    }

    private IotCallbackLog saveLog(String tenantId, String action, String appId, String eventId,
                                   int signOk, String body, String ip, String status,
                                   String error, int duplicate) {
        IotCallbackLog l = new IotCallbackLog();
        l.setId(idGen.nextId());
        l.setTenantId(tenantId);
        l.setAppId(appId);
        l.setMsgType(action);
        l.setEventId(eventId == null ? "" : eventId);
        l.setSignOk(signOk);
        l.setRawBody(trim(body, 2000));
        l.setSourceIp(ip);
        l.setIsDuplicate(duplicate);
        l.setProcessStatus(status);
        l.setErrorMsg(error);
        l.setReceiveTime(LocalDateTime.now());
        l.setCreateTime(LocalDateTime.now());
        try {
            logMapper.insert(l);
            return l;
        } catch (DuplicateKeyException dup) {
            return null;
        }
    }

    private void updateLog(IotCallbackLog l, String status, String error) {
        l.setProcessStatus(status);
        l.setErrorMsg(error);
        logMapper.updateById(l);
    }

    private boolean saveNonce(String tenantId, String appId, String nonce) {
        IotNonce n = new IotNonce();
        n.setId(idGen.nextId());
        n.setTenantId(tenantId);
        n.setAppId(appId == null ? "unknown" : appId);
        n.setNonce(nonce);
        n.setExpireAt(LocalDateTime.now().plusMinutes(settings.nonceCacheMinutes()));
        n.setCreateTime(LocalDateTime.now());
        try {
            nonceMapper.insert(n);
            return true;
        } catch (DuplicateKeyException dup) {
            return false;
        }
    }

    private static String text(JsonNode n, String field) {
        JsonNode v = n.get(field);
        return v == null || v.isNull() ? null : v.asText();
    }

    private static Integer intVal(JsonNode n, String field, Integer def) {
        JsonNode v = n.get(field);
        return v == null || v.isNull() ? def : v.asInt(def == null ? 0 : def);
    }

    private static Long longVal(JsonNode n, String field) {
        JsonNode v = n.get(field);
        if (v == null || v.isNull()) {
            return null;
        }
        try {
            return Long.valueOf(v.asText());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static LocalDateTime parseTime(String s) {
        if (s == null || s.isBlank()) {
            return null;
        }
        String t = s.trim().replace('T', ' ');
        if (t.length() > 19) {
            t = t.substring(0, 19);
        }
        try {
            return LocalDateTime.parse(t, FMT);
        } catch (Exception e) {
            try {
                return LocalDateTime.parse(t);
            } catch (Exception ignore) {
                return null;
            }
        }
    }

    private static String trim(String s, int max) {
        if (s == null) {
            return null;
        }
        return s.length() <= max ? s : s.substring(0, max);
    }

    /** 回调响应。 */
    public record Reply(int httpStatus, String code, String message) {
        public Map<String, Object> body() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("code", code);
            m.put("message", message);
            return m;
        }
    }
}
''')

# ---------------- 回调控制器 ----------------
write('iot/gateway/IotCallbackController.java', '''package com.yundao.bp.iot.gateway;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * IoT 平台回调统一入口。
 *
 * <p>路径：{@code /api/callback/iot/{action}}，action 见 {@code IotCallbackService#dispatch}。
 * 该路径不走登录鉴权，改用 HMAC 验签 + Nonce 防重放。
 */
@RestController
@RequestMapping("/api/callback/iot")
public class IotCallbackController {

    private final IotCallbackService service;

    public IotCallbackController(IotCallbackService service) {
        this.service = service;
    }

    @PostMapping("/{action:.+}")
    public ResponseEntity<Map<String, Object>> callback(
            @PathVariable String action,
            @RequestBody(required = false) String body,
            HttpServletRequest req) {
        IotCallbackService.Reply reply = service.handle(
                action,
                body == null ? "{}" : body,
                req.getHeader("X-Iot-AppId"),
                req.getHeader("X-Iot-Timestamp"),
                req.getHeader("X-Iot-Nonce"),
                req.getHeader("X-Iot-Signature"),
                req.getRemoteAddr(),
                req.getHeader("X-Tenant-Id"));
        return ResponseEntity.status(reply.httpStatus()).body(reply.body());
    }
}
''')

print('回调服务与控制器完成')
