package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 报表定义。对应 `bp_rpt_report_def`。
 */
@Data
@TableName("bp_rpt_report_def")
public class RptReportDef {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String reportCode;
    private String reportName;
    /** HOUSE / PERSON / CONTRACT / FINANCE / DEVICE / WORKORDER */
    private String reportType;
    private String scenario;
    /** 查询配置 JSON（数据源、字段、条件） */
    private String queryConfig;
    /** 列配置 JSON */
    private String columnConfig;
    /** EXCEL / CSV / PDF */
    private String exportFormat;
    private String reportStatus;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
