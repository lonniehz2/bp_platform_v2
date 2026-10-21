package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 系统参数。对应 `bp_sys_config`。
 *
 * <p>用途：把政策参数（公示天数、禁申年限、过渡期月数、加价倍率等）
 * 从硬编码改为可配置，支持分地区差异。
 */
@Data
@TableName("bp_sys_config")
public class SysConfig {

    @TableId(type = IdType.INPUT)
    private Long id;

    /** 租户ID（NULL 表示全局） */
    private String tenantId;
    private String configKey;
    private String configValue;
    /** SYSTEM / BUSINESS / IOT / NOTIFY / SECURITY */
    private String configGroup;
    /** STRING / INT / DECIMAL / BOOL / JSON */
    private String valueType;
    private Integer isEncrypted;
    private Integer isSystem;
    private String description;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
