package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 能耗策略 */
@Data
@TableName("bp_fin_energy_policy")
public class EnergyPolicy {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long orgId;
    private String vacancyBearer;
    private BigDecimal warnRate;
    private BigDecimal alarmRate;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
