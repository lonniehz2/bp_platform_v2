package com.yundao.bp.gov.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 政务适配器调用日志。对应 `bp_gov_adapter_log`。
 */
@Data
@TableName("bp_gov_adapter_log")
public class GovAdapterLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String adapterCode;
    private String traceId;
    private String bizType;
    private Long bizId;
    private String requestBody;
    private String responseBody;
    private Integer successFlag;
    private String errorMsg;
    private Integer durationMs;
    private LocalDateTime callTime;
    private LocalDateTime createTime;
}
