package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 能耗分摊主单 */
@Data
@TableName("bp_fin_utility_allocation")
public class UtilityAllocation {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long meterPointId;
    private String period;
    private BigDecimal startReading;
    private BigDecimal endReading;
    private BigDecimal totalUsage;
    private BigDecimal totalAmount;
    private BigDecimal operatorBearAmount;
    private String tierDetail;
    private String status;
    private LocalDateTime createTime;
}
