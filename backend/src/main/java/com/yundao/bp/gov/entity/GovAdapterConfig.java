package com.yundao.bp.gov.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 政务系统适配器配置。对应 `bp_gov_adapter_config`。
 */
@Data
@TableName("bp_gov_adapter_config")
public class GovAdapterConfig {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String adapterCode;
    private String adapterName;
    /** PUBLIC_HOUSING / POLICE / HOUSING / REAL_ESTATE */
    private String systemType;
    /** HTTP / WEBSOCKET / FILE / SFTP / DB */
    private String protocol;
    private String endpoint;
    /** NONE / APPKEY / TOKEN / BASIC / CERT / SIGN */
    private String authType;
    /** 鉴权配置 JSON（敏感，不对外返回） */
    private String authConfig;
    private Integer timeoutMs;
    private Integer retryTimes;
    private Integer qpsLimit;
    /** RETRY / MANUAL / FILE / BLOCK */
    private String degradeMode;
    /** ENABLED / DISABLED */
    private String adapterStatus;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
