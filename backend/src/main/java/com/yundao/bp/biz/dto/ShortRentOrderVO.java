package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ShortRentOrderStatus;
import com.yundao.bp.biz.entity.BizShortRentOrder;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 短租订单视图。
 */
public record ShortRentOrderVO(
        Long id,
        String orderNo,
        Long orgId,
        Long houseId,
        Long spaceId,
        String sourceChannel,
        String guestName,
        String guestPhone,
        Integer guestCount,
        LocalDateTime checkInTime,
        LocalDateTime checkOutTime,
        Integer nightCount,
        BigDecimal roomAmount,
        BigDecimal extraAmount,
        BigDecimal discountAmount,
        BigDecimal totalAmount,
        BigDecimal paidAmount,
        String orderStatus,
        String orderStatusLabel,
        String payStatus,
        String cancelReason,
        String remark,
        /** 派生：订单占用的日期区间（日历口径，左闭右开） */
        LocalDate occupyFrom,
        LocalDate occupyTo,
        /** 派生：待收金额 = 总额 - 已付 */
        BigDecimal unpaidAmount,
        /** 派生：是否已过退房时刻但仍是"已入住"（超时未退房） */
        Boolean overdueCheckout,
        LocalDateTime createTime
) {
    public static ShortRentOrderVO from(BizShortRentOrder e) {
        if (e == null) {
            return null;
        }
        ShortRentOrderStatus st;
        try {
            st = ShortRentOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            st = ShortRentOrderStatus.PENDING;
        }
        LocalDate from = e.getCheckInTime() == null ? null : e.getCheckInTime().toLocalDate();
        LocalDate to = e.getCheckOutTime() == null ? null : e.getCheckOutTime().toLocalDate();
        BigDecimal total = e.getTotalAmount() == null ? BigDecimal.ZERO : e.getTotalAmount();
        BigDecimal paid = e.getPaidAmount() == null ? BigDecimal.ZERO : e.getPaidAmount();
        boolean overdue = st == ShortRentOrderStatus.CHECKED_IN
                && e.getCheckOutTime() != null
                && LocalDateTime.now().isAfter(e.getCheckOutTime());
        return new ShortRentOrderVO(e.getId(), e.getOrderNo(), e.getOrgId(), e.getHouseId(),
                e.getSpaceId(), e.getSourceChannel(), e.getGuestName(), e.getGuestPhone(),
                e.getGuestCount(), e.getCheckInTime(), e.getCheckOutTime(), e.getNightCount(),
                e.getRoomAmount(), e.getExtraAmount(), e.getDiscountAmount(), e.getTotalAmount(),
                e.getPaidAmount(), e.getOrderStatus(), st.label(), e.getPayStatus(),
                e.getCancelReason(), e.getRemark(), from, to, total.subtract(paid), overdue,
                e.getCreateTime());
    }
}
