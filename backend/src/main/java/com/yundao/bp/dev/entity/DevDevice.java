package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 设备台账。对应 {@code bp_dev_device}。
 *
 * <p>⭐ <b>设备-空间绑定关系就靠 {@code spaceId}</b>（安装空间），
 * 层级继承通过空间树的 {@code path_code} 前缀实现，无需额外绑定表。
 */
@Data
@TableName("bp_dev_device")
public class DevDevice {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;

    /** IoT 平台侧设备标识（门锁即 lockId） */
    private String deviceId;
    private String deviceMac;
    private String deviceName;

    /** LOCK / ACCESS / ELEVATOR / GATE / METER_* / ... 见 OpenableDeviceType */
    private String deviceType;
    private String deviceModel;
    private String lockType;
    private String ventor;

    private Long orgId;

    /** 产权方组织（设备归谁所有） */
    private Long ownerOrgId;

    /** 维保方组织（谁负责维修） */
    private Long maintainOrgId;
    /** 安装空间（绑定锚点） */
    private Long spaceId;
    private String installAddress;
    private LocalDateTime installTime;

    private Integer onlineStatus;
    private LocalDateTime onlineTime;
    private LocalDateTime offlineTime;

    /** 最后一次上报时间（属性/事件/心跳均可刷新） */
    private LocalDateTime lastReportTime;
    private Integer battery;
    private String rssi;

    /** 是否公有设备（小区大门等，通常对所有住户开放） */
    private Integer isPublic;

    private Long ownerPersonId;
    private Long adminPersonId;
    private Long usablePersonId;
    private String agentCode;

    /** NORMAL / MAINTENANCE / SCRAPPED / UNKNOWN */
    private String deviceStatus;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
