package com.yundao.bp.asset.service;

import com.yundao.bp.asset.dto.AvailabilityVO;
import com.yundao.bp.asset.dto.BookCmd;
import com.yundao.bp.asset.dto.DayCellVO;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.List;

/**
 * 房源日房态与预订服务（短租业态支撑）。
 *
 * <p><b>核心保证</b>：同一房源同一天<b>不会</b>被两个单据占用。
 * 实现方式是"库唯一索引 + 预订前逐日检查可售"。
 */
public interface HouseCalendarService {

    /** 铺日历：把指定月份内缺失的日期补齐为 AVAILABLE（幂等）。返回新增天数。 */
    int ensureMonth(Long houseId, YearMonth month);

    /** 补齐区间内所有日期（缺失则建 AVAILABLE）。 */
    int ensureRange(Long houseId, LocalDate start, LocalDate end);

    /** 查某房源某月的月历。 */
    List<DayCellVO> getMonth(Long houseId, YearMonth month);

    /** 查询某房源在指定区间的可售情况（[checkIn, checkOut)）。 */
    AvailabilityVO availability(Long houseId, LocalDate checkIn, LocalDate checkOut);

    /** 批量查询某组织下在指定区间整段可售的房源。 */
    List<AvailabilityVO> searchAvailable(Long orgId, LocalDate checkIn, LocalDate checkOut);

    /**
     * 预订/占用（[checkIn, checkOut) 左闭右开）。
     *
     * <p>逐日校验必须为 AVAILABLE，任何一天被占用则<b>整单拒绝</b>（不产生部分占用）。
     */
    int book(BookCmd cmd);

    /**
     * 把已预订的日期置为"已入住"（BOOKED → OCCUPIED）。
     *
     * <p>只更新处于 BOOKED 且 bookingId 匹配的日期；返回更新天数。
     */
    int markOccupied(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId);

    /** 释放占用（按 bookingId 匹配，避免误放他人）。返回释放天数。 */
    int release(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId);

    /** 手工设置某几日房态（停售/维修）。 */
    int setStatus(Long houseId, LocalDate start, LocalDate end, String dayStatus,
                  String remark);

    /** 手工改某一天的当日价（节假日调价）。 */
    DayCellVO setPrice(Long houseId, LocalDate date, java.math.BigDecimal price);

    /**
     * 区间改价：把 [start, end] 的价格改为 price；weekendPrice 非空时，
     * 周六/周日用 weekendPrice 覆盖（酒店平日/周末差价）。
     *
     * <p>已占用（BOOKED/OCCUPIED）的日期不改价，避免影响已成交订单。
     *
     * @return 实际更新的天数
     */
    int setPriceRange(Long houseId, java.time.LocalDate start, java.time.LocalDate end,
                      java.math.BigDecimal price, java.math.BigDecimal weekendPrice);
}
