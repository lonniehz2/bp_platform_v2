package com.yundao.bp.gov.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 监管报送任务。对应 `bp_gov_report_task`。
 */
@Data
@TableName("bp_gov_report_task")
public class GovReportTask {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String taskNo;
    /** PUBLIC_HOUSING / POLICE / HOUSING / REAL_ESTATE */
    private String targetSystem;
    /** HOUSE / TENANT / STATUS / CONTRACT / FINANCE / ACCESS */
    private String reportType;
    /** API / FILE / MANUAL */
    private String reportMode;
    /** REALTIME / DAILY / MONTHLY / QUARTERLY / ONCE */
    private String reportCycle;
    /** 数据范围 JSON（时间跨度/组织范围） */
    private String dataRange;
    private Integer recordCount;
    private Integer successCount;
    private Integer failCount;
    private String fileUrl;
    /** PENDING / RUNNING / SUCCESS / PARTIAL / FAILED */
    private String taskStatus;
    private String failDetail;
    private LocalDateTime reportTime;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
