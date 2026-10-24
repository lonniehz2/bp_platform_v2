# -*- coding: utf-8 -*-
"""统一设备事件/告警表：低电量、防拆、试错、胁迫、开锁、上下线、超功率等。

设计参考泊寓 IoT 文档的事件模型：{did, identifier, time, body}。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev')

ENTITY = '''package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 设备事件/告警。对应表 {@code bp_dev_event}。
 *
 * <p>统一承载 IoT 上报的各类事件，identifier 见 {@code DevEventType}：
 * 低电量、防拆、试错、胁迫、开锁、上下线、超功率、本地合闸等。
 */
@TableName("bp_dev_event")
public class DevEvent {

    @TableId
    private Long id;

    private String tenantId;

    private Long orgId;

    private Long spaceId;

    /** 设备编号（IoT 侧 did） */
    private String deviceId;

    /** 事件类型，见 DevEventType */
    private String identifier;

    /** INFO / WARN / CRITICAL */
    private String eventLevel;

    private LocalDateTime eventTime;

    /** 事件原始载荷（JSON 字符串） */
    private String body;

    private Integer handled;

    private String handleRemark;

    private LocalDateTime handleTime;

    private String handleBy;

    private Integer isDeleted;

    private LocalDateTime createTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTenantId() { return tenantId; }
    public void setTenantId(String tenantId) { this.tenantId = tenantId; }

    public Long getOrgId() { return orgId; }
    public void setOrgId(Long orgId) { this.orgId = orgId; }

    public Long getSpaceId() { return spaceId; }
    public void setSpaceId(Long spaceId) { this.spaceId = spaceId; }

    public String getDeviceId() { return deviceId; }
    public void setDeviceId(String deviceId) { this.deviceId = deviceId; }

    public String getIdentifier() { return identifier; }
    public void setIdentifier(String identifier) { this.identifier = identifier; }

    public String getEventLevel() { return eventLevel; }
    public void setEventLevel(String eventLevel) { this.eventLevel = eventLevel; }

    public LocalDateTime getEventTime() { return eventTime; }
    public void setEventTime(LocalDateTime eventTime) { this.eventTime = eventTime; }

    public String getBody() { return body; }
    public void setBody(String body) { this.body = body; }

    public Integer getHandled() { return handled; }
    public void setHandled(Integer handled) { this.handled = handled; }

    public String getHandleRemark() { return handleRemark; }
    public void setHandleRemark(String handleRemark) { this.handleRemark = handleRemark; }

    public LocalDateTime getHandleTime() { return handleTime; }
    public void setHandleTime(LocalDateTime handleTime) { this.handleTime = handleTime; }

    public String getHandleBy() { return handleBy; }
    public void setHandleBy(String handleBy) { this.handleBy = handleBy; }

    public Integer getIsDeleted() { return isDeleted; }
    public void setIsDeleted(Integer isDeleted) { this.isDeleted = isDeleted; }

    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
}
'''

TYPE_ENUM = '''package com.yundao.bp.dev.constant;

/**
 * 设备事件类型。
 *
 * <p>告警类（LOW_BATTERY / TAMPER / TRIAL_ERROR / DURESS / POWER_OVER）会进入告警视图，
 * 其余为记录类事件。
 */
public enum DevEventType {

    OPEN("开锁", "INFO", false),
    ONLINE("上线", "INFO", false),
    OFFLINE("离线", "WARN", true),
    LOW_BATTERY("低电量告警", "WARN", true),
    BATTERY_RESTORED("低电解除", "INFO", false),
    TAMPER("防拆告警", "CRITICAL", true),
    TRIAL_ERROR("试错告警（密码连续错误）", "WARN", true),
    DURESS("胁迫告警", "CRITICAL", true),
    POWER_OVER("超功率告警", "WARN", true),
    LOCAL_SWITCH("本地合闸", "INFO", false),
    METER_READ("抄表读数", "INFO", false),
    OTHER("其他", "INFO", false);

    private final String label;
    private final String defaultLevel;
    private final boolean alarm;

    DevEventType(String label, String defaultLevel, boolean alarm) {
        this.label = label;
        this.defaultLevel = defaultLevel;
        this.alarm = alarm;
    }

    public String label() { return label; }
    public String defaultLevel() { return defaultLevel; }
    public boolean alarm() { return alarm; }

    public static DevEventType of(String code) {
        if (code == null) {
            return OTHER;
        }
        for (DevEventType t : values()) {
            if (t.name().equalsIgnoreCase(code)) {
                return t;
            }
        }
        return OTHER;
    }
}
'''

MAPPER = '''package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevEvent;
import org.apache.ibatis.annotations.Mapper;

/** 设备事件。 */
@Mapper
public interface DevEventMapper extends BaseMapper<DevEvent> {
}
'''

CONTROLLER = '''package com.yundao.bp.dev.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.constant.DevEventType;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.mapper.DevEventMapper;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 设备事件与告警。
 *
 * <p>承载低电量、防拆、试错、胁迫等告警，以及开锁、上下线等记录类事件。
 * 事件由 IoT 平台上报（{@code POST /dev-events}），业务侧查询与处理。
 */
@RestController
@RequestMapping("/api/v1/dev-events")
public class DevEventController {

    private final DevEventMapper mapper;
    private final DevDeviceMapper deviceMapper;
    private final SnowflakeIdGenerator idGen;

    public DevEventController(DevEventMapper mapper, DevDeviceMapper deviceMapper,
                              SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.deviceMapper = deviceMapper;
        this.idGen = idGen;
    }

    /** 分页查询事件；alarmOnly=true 只看告警类。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping
    public R<PageResult<DevEvent>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String identifier,
            @RequestParam(required = false) String eventLevel,
            @RequestParam(required = false) Integer handled,
            @RequestParam(required = false) Boolean alarmOnly) {
        LambdaQueryWrapper<DevEvent> qw = new LambdaQueryWrapper<DevEvent>()
                .eq(deviceId != null && !deviceId.isBlank(), DevEvent::getDeviceId, deviceId)
                .eq(identifier != null && !identifier.isBlank(), DevEvent::getIdentifier, identifier)
                .eq(eventLevel != null && !eventLevel.isBlank(), DevEvent::getEventLevel, eventLevel)
                .eq(handled != null, DevEvent::getHandled, handled)
                .orderByDesc(DevEvent::getEventTime)
                .orderByDesc(DevEvent::getId);
        if (Boolean.TRUE.equals(alarmOnly)) {
            List<String> alarms = new ArrayList<>();
            for (DevEventType t : DevEventType.values()) {
                if (t.alarm()) {
                    alarms.add(t.name());
                }
            }
            qw.in(DevEvent::getIdentifier, alarms);
        }
        IPage<DevEvent> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords()));
    }

    /** 事件上报（IoT 回调）。同一 did + identifier + eventTime 幂等。 */
    @PostMapping
    public R<DevEvent> report(@RequestBody EventCmd cmd) {
        if (cmd.deviceId() == null || cmd.identifier() == null) {
            throw BizException.paramInvalid("deviceId 与 identifier 不能为空");
        }
        DevEventType type = DevEventType.of(cmd.identifier());
        DevEvent e = new DevEvent();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setDeviceId(cmd.deviceId());
        e.setIdentifier(type.name());
        e.setEventLevel(cmd.eventLevel() == null || cmd.eventLevel().isBlank()
                ? type.defaultLevel() : cmd.eventLevel());
        e.setEventTime(cmd.eventTime() == null ? LocalDateTime.now() : cmd.eventTime());
        e.setBody(cmd.body());
        e.setHandled(0);
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        DevDevice d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceId, cmd.deviceId()).last("LIMIT 1"));
        if (d != null) {
            e.setOrgId(d.getOrgId());
            e.setSpaceId(d.getSpaceId());
        }
        mapper.insert(e);
        return R.ok(e);
    }

    /** 标记已处理。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/{id}/handle")
    public R<DevEvent> handle(@PathVariable Long id, @RequestBody(required = false) HandleCmd cmd) {
        DevEvent e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("设备事件");
        }
        e.setHandled(1);
        e.setHandleRemark(cmd == null ? null : cmd.remark());
        e.setHandleTime(LocalDateTime.now());
        e.setHandleBy(String.valueOf(TenantContext.userId()));
        mapper.updateById(e);
        return R.ok(e);
    }

    /** 告警统计：按类型与级别。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/stats")
    public R<Map<String, Object>> stats(@RequestParam(required = false) Boolean unhandledOnly) {
        LambdaQueryWrapper<DevEvent> qw = new LambdaQueryWrapper<>();
        if (Boolean.TRUE.equals(unhandledOnly)) {
            qw.eq(DevEvent::getHandled, 0);
        }
        List<DevEvent> all = mapper.selectList(qw);
        Map<String, Integer> byType = new LinkedHashMap<>();
        Map<String, Integer> byLevel = new LinkedHashMap<>();
        for (DevEvent e : all) {
            byType.merge(e.getIdentifier(), 1, Integer::sum);
            byLevel.merge(e.getEventLevel(), 1, Integer::sum);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", all.size());
        out.put("unhandled", all.stream().filter(x -> x.getHandled() == null
                || x.getHandled() == 0).count());
        out.put("byType", byType);
        out.put("byLevel", byLevel);
        out.put("alarmTypes", java.util.Arrays.stream(DevEventType.values())
                .filter(DevEventType::alarm)
                .map(t -> Map.of("code", t.name(), "label", t.label(),
                        "level", t.defaultLevel()))
                .toList());
        return R.ok(out);
    }

    public record EventCmd(String deviceId, String identifier, String eventLevel,
                           LocalDateTime eventTime, String body) {
    }

    public record HandleCmd(String remark) {
    }
}
'''

for path, content in [
    (os.path.join(J, 'entity', 'DevEvent.java'), ENTITY),
    (os.path.join(J, 'constant', 'DevEventType.java'), TYPE_ENUM),
    (os.path.join(J, 'mapper', 'DevEventMapper.java'), MAPPER),
    (os.path.join(J, 'controller', 'DevEventController.java'), CONTROLLER),
]:
    if os.path.exists(path):
        print('已存在', os.path.basename(path))
        continue
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='').write(content)
    print('已创建', os.path.basename(path))
