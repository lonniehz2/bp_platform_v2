# -*- coding: utf-8 -*-
"""生成 日房态与预订 模块"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['asset/constant/DayStatus.java'] = '''package com.yundao.bp.asset.constant;

import java.util.Set;

/**
 * 日房态（对应 {@code bp_asset_house_calendar.day_status}）。
 *
 * <p>⭐ <b>短租业态的基石</b>：长租用"房源整体状态"，短租必须"按天"表达可售性，
 * 否则同一天会被重复售卖。
 *
 * <pre>
 *   AVAILABLE 可售 ──预订──> BOOKED 已预订 ──入住──> OCCUPIED 已入住
 *        │                                          │
 *        ├──停售──> CLOSED                          └──退房──> AVAILABLE
 *        └──维修──> MAINTENANCE ──修复──> AVAILABLE
 * </pre>
 */
public enum DayStatus {

    AVAILABLE("可售"),
    BOOKED("已预订"),
    OCCUPIED("已入住"),
    CLOSED("停售"),
    MAINTENANCE("维修");

    private final String label;

    DayStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否可被预订/占用。 */
    public boolean bookable() {
        return this == AVAILABLE;
    }

    /** 是否由业务单据占用（预订/合同），释放时需匹配来源。 */
    public boolean occupied() {
        return this == BOOKED || this == OCCUPIED;
    }

    /** 允许的迁移。 */
    public static Set<DayStatus> nextOf(DayStatus from) {
        return switch (from) {
            case AVAILABLE -> Set.of(BOOKED, OCCUPIED, CLOSED, MAINTENANCE);
            case BOOKED -> Set.of(OCCUPIED, AVAILABLE, CLOSED);
            case OCCUPIED -> Set.of(AVAILABLE, MAINTENANCE);
            case CLOSED -> Set.of(AVAILABLE);
            case MAINTENANCE -> Set.of(AVAILABLE);
        };
    }
}
'''

FILES['asset/entity/AssetHouseCalendar.java'] = '''package com.yundao.bp.asset.entity;

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
'''

FILES['asset/mapper/AssetHouseCalendarMapper.java'] = '''package com.yundao.bp.asset.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.asset.entity.AssetHouseCalendar;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AssetHouseCalendarMapper extends BaseMapper<AssetHouseCalendar> {
}
'''

FILES['asset/dto/BookCmd.java'] = '''package com.yundao.bp.asset.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

/**
 * 预订/占用房源（按日）。
 *
 * <p><b>区间语义</b>：{@code [checkIn, checkOut)} —— <b>左闭右开</b>。
 * 例如 11-01 入住、11-03 退房，占据 11-01、11-02 两天，11-03 当天可再售。
 * 这是酒店/民宿的通用口径。
 */
public record BookCmd(

        @NotNull(message = "房源不能为空")
        Long houseId,

        @NotNull(message = "入住日不能为空")
        LocalDate checkIn,

        @NotNull(message = "退房日不能为空")
        LocalDate checkOut,

        /** 占用单据ID（预订单/合同ID） */
        Long bookingId,

        /** BOOKING / CONTRACT / MANUAL */
        String sourceType,

        /** 占用后的房态：BOOKED（预订）或 OCCUPIED（直接入住） */
        String targetStatus,

        String remark
) {
}
'''

FILES['asset/dto/DayCellVO.java'] = '''package com.yundao.bp.asset.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 月历中的一天。
 */
public record DayCellVO(
        LocalDate date,
        String dayStatus,
        String dayStatusLabel,
        BigDecimal price,
        Long bookingId,
        String sourceType,
        String remark
) {
}
'''

FILES['asset/dto/AvailabilityVO.java'] = '''package com.yundao.bp.asset.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * 可售查询结果。
 *
 * @param houseId    房源
 * @param houseCode  房源编号
 * @param houseName  房源名称
 * @param days       查询天数
 * @param freeDays   期间可售天数
 * @param available  是否整段可售
 * @param totalPrice 期间合计价（取日历当日价，缺失则 null）
 */
public record AvailabilityVO(
        Long houseId,
        String houseCode,
        String houseName,
        int days,
        int freeDays,
        boolean available,
        BigDecimal totalPrice,
        List<DayCellVO> cells
) {
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
