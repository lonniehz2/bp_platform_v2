package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/** 能耗抄表读数（水电燃气等 METER 类收费）。 */
@Data
@TableName("bp_fin_meter_reading")
public class FinMeterReading {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    private Long houseId;
    private Long feeItemId;

    /** 计量来源设备（用于溯源，可为空=人工录入） */
    private String deviceId;
    private LocalDate readDate;
    private BigDecimal reading;
    private BigDecimal prevReading;
    /** 倍率：用量 =（本次−上次）× 倍率 */
    private BigDecimal multiplier;
    /** 单位：kWh / m3 */
    private String unit;
    private BigDecimal usageAmount;
    private BigDecimal unitPrice;
    private BigDecimal amount;
    private String billStatus;
    private Long billId;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private Integer isDeleted;
}
