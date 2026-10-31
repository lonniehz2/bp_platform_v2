package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 表计点位 */
@Data
@TableName("bp_fin_meter_point")
public class MeterPoint {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long spaceId;
    private Long feeItemId;
    private String meterScope;
    private String allocationBasis;
    private Integer bedCapacity;
    private String meterName;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
