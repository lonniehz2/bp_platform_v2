package com.yundao.bp.gov.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 监管报送明细。对应 `bp_gov_report_detail`。
 */
@Data
@TableName("bp_gov_report_detail")
public class GovReportDetail {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long taskId;
    private String bizType;
    private Long bizId;
    /** 外部系统 ID（回写，便于对账） */
    private String externalId;
    /** PENDING / SUCCESS / FAILED / SKIPPED */
    private String syncStatus;
    private String errorCode;
    private String errorMsg;
    private String requestData;
    private String responseData;
    private LocalDateTime createTime;
}
