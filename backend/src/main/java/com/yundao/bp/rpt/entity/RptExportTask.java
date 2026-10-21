package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 导出任务。对应 `bp_rpt_export_task`。
 */
@Data
@TableName("bp_rpt_export_task")
public class RptExportTask {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String taskNo;
    private String exportType;
    private String reportCode;
    private String queryParams;
    private String fileName;
    private String fileUrl;
    private Long fileSize;
    private Integer rowCount;
    /** PENDING / RUNNING / SUCCESS / FAILED */
    private String taskStatus;
    private Integer progress;
    private String failReason;
    private LocalDateTime expireTime;
    private Long userId;
    private LocalDateTime createTime;
    private LocalDateTime finishTime;
}
