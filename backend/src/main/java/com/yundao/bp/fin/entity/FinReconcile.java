package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 财务对账记录。对应 {@code bp_fin_reconcile}。
 */
@Data
@TableName("bp_fin_reconcile")
public class FinReconcile {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String reconcileNo;
    private Long accountSetId;

    private LocalDate reconcileDate;
    /** CHANNEL / DAILY / MANUAL */
    private String reconcileType;
    private String payChannel;

    /** 系统金额 */
    private BigDecimal systemAmount;
    /** 渠道金额 */
    private BigDecimal channelAmount;
    /** 差异金额 = 系统 - 渠道 */
    private BigDecimal diffAmount;
    private Integer diffCount;

    /** MATCHED / DIFF / HANDLED */
    private String reconcileStatus;
    private String diffDetailUrl;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
