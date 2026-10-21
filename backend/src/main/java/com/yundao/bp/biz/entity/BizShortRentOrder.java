package com.yundao.bp.biz.entity;

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
 * 短租订单。对应 {@code bp_biz_short_rent_order}。
 *
 * <p>与长租合同的区别：<b>时刻级</b>入住/退房 + <b>房晚</b>计价 + 实名登记。
 */
@Data
@TableName("bp_biz_short_rent_order")
public class BizShortRentOrder {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String orderNo;
    private Long orgId;
    private Long houseId;
    private Long spaceId;

    /** DIRECT / OTA / WECHAT / PHONE / WALKIN / OTHER */
    private String sourceChannel;

    private String guestName;
    private String guestPhone;
    /** 证件号（加密存储） */
    private String guestIdCard;
    private Integer guestCount;

    /** 入住时刻（精确到时分） */
    private LocalDateTime checkInTime;
    /** 退房时刻（精确到时分） */
    private LocalDateTime checkOutTime;
    /** 房晚数 */
    private Integer nightCount;

    private BigDecimal roomAmount;
    private BigDecimal extraAmount;
    private BigDecimal discountAmount;
    private BigDecimal totalAmount;
    private BigDecimal paidAmount;

    /** PENDING / CONFIRMED / CHECKED_IN / CHECKED_OUT / CANCELLED / NO_SHOW */
    private String orderStatus;
    /** UNPAID / PAID / REFUNDED */
    private String payStatus;

    private String cancelReason;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
