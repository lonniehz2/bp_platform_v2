package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 指标小时汇总。对应 `bp_rpt_metric_hourly`。
 */
@Data
@TableName("bp_rpt_metric_hourly")
public class RptMetricHourly {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private LocalDateTime statHour;
    private Long orgId;
    private String metricCode;
    private BigDecimal metricValue;
    private LocalDateTime createTime;
}
