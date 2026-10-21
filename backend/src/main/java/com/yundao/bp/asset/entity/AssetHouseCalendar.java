package com.yundao.bp.asset.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 房源日房态。对应 {@code bp_asset_house_calendar}。
 *
 * <p>一行 = 一个房源的一天。短租（酒店/民宿/网约房）靠它判断"某天能不能卖"。
 */
@Data
@TableName("bp_asset_house_calendar")
public class AssetHouseCalendar {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    private Long houseId;
    private LocalDate calDate;

    /** AVAILABLE / BOOKED / OCCUPIED / CLOSED / MAINTENANCE */
    private String dayStatus;
    /** 当日价（空=用规则默认价，用于节假日调价） */
    private BigDecimal priceOverride;
    private Long bookingId;
    /** BOOKING / CONTRACT / MANUAL */
    private String sourceType;
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
