package com.yundao.bp.dev.entity;

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

    /** IoT 事件唯一号（幂等键） */
    private String eventId;

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

    public String getEventId() { return eventId; }
    public void setEventId(String eventId) { this.eventId = eventId; }

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
