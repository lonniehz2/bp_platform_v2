package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 滞纳金策略 */
@Data
@TableName("bp_fin_late_fee_policy")
public class LateFeePolicy {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long orgId;
    private BigDecimal dailyRate;
    private Integer graceDays;
    private BigDecimal capRate;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
