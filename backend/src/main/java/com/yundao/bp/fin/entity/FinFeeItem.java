package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 收费项目。对应 {@code bp_fin_fee_item}。
 */
@Data
@TableName("bp_fin_fee_item")
public class FinFeeItem {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String itemCode;
    private String itemName;

    /** RENT / PROPERTY / PARKING / ENERGY / DEPOSIT / LATE_FEE / OTHER */
    private String itemType;
    /** 适用保障类型（NULL 通用） */
    private String securityType;
    /** FIXED / BY_AREA / BY_HOUSE / BY_PERSON / BY_BED / BY_NIGHT / METER */
    private String calcMode;
    private BigDecimal unitPrice;
    private String unit;

    /** ENABLED / DISABLED */
    private String status;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
