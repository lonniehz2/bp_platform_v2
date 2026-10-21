package com.yundao.bp.asset.dto;

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
