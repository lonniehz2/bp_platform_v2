package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 能耗分摊明细 */
@Data
@TableName("bp_fin_utility_share")
public class UtilityShare {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long allocationId;
    private Long contractId;
    private Long personId;
    private Integer occupyDays;
    private BigDecimal personDays;
    private BigDecimal shareRatio;
    private BigDecimal shareAmount;
    private BigDecimal roundingDelta;
    private Long billId;
}
