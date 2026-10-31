package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 总表分表月度统计 */
@Data
@TableName("bp_fin_energy_monthly_stat")
public class EnergyMonthlyStat {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String period;
    private Long feeItemId;
    private Long spaceId;
    private BigDecimal totalUsage;
    private BigDecimal submeterUsage;
    private BigDecimal diffUsage;
    private BigDecimal diffRate;
    private String alertLevel;
    private LocalDateTime createTime;
}
