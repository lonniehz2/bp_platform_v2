package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 指标日汇总。对应 `bp_rpt_metric_daily`。
 */
@Data
@TableName("bp_rpt_metric_daily")
public class RptMetricDaily {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private LocalDate statDate;
    private Long orgId;
    private String metricCode;
    private String metricName;
    private BigDecimal metricValue;
    private String metricUnit;
    private String dimensionJson;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
