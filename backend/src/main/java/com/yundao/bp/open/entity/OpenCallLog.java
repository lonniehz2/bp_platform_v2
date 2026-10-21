package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 开放接口调用日志。对应 `bp_open_call_log`（无 tenant_id，按 appKey 归属）。
 */
@Data
@TableName("bp_open_call_log")
public class OpenCallLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String appKey;
    private String apiCode;
    private String apiPath;
    private String requestId;
    private String clientIp;
    /** 请求体（已脱敏） */
    private String requestBody;
    private String responseCode;
    private Integer successFlag;
    private String errorMsg;
    private Integer durationMs;
    private LocalDateTime callTime;
    private LocalDateTime createTime;
}
