package com.yundao.bp.asset.dto;

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
