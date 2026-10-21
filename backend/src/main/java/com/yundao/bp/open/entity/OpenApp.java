package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 开放平台应用。对应 `bp_open_app`。
 */
@Data
@TableName("bp_open_app")
public class OpenApp {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    /** AppKey（公开展示，用于标识应用） */
    private String appKey;
    /** AppSecret（加密存储；仅在创建/重置时明文返回一次） */
    private String appSecret;
    private String appName;
    /** THIRD_PARTY / INTERNAL / GOV */
    private String appType;
    private String ownerOrg;
    private String contactName;
    private String contactPhone;
    /** IP 白名单（逗号分隔，为空表示不限制） */
    private String ipWhitelist;
    /** QPS 限流 */
    private Integer qpsLimit;
    /** 日调用配额（空=不限） */
    private Integer dailyQuota;
    /** 授权接口范围（逗号分隔，* 表示全部） */
    private String scopeCodes;
    private LocalDate expireDate;
    /** ENABLED / DISABLED / EXPIRED */
    private String appStatus;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
