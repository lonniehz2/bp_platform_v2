package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.RefundStatus;
import com.yundao.bp.fin.entity.FinRefund;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 退款单视图。
 */
public record RefundVO(
        Long id,
        String refundNo,
        Long paymentId,
        Long personId,
        Long contractId,
        BigDecimal refundAmount,
        String refundReason,
        String refundType,
        String refundChannel,
        String refundStatus,
        String refundStatusLabel,
        Long approveById,
        LocalDateTime approveTime,
        LocalDateTime refundTime,
        LocalDateTime createTime
) {
    public static RefundVO from(FinRefund e) {
        if (e == null) {
            return null;
        }
        RefundStatus st;
        try {
            st = RefundStatus.valueOf(e.getRefundStatus());
        } catch (IllegalArgumentException ex) {
            st = RefundStatus.PENDING;
        }
        return new RefundVO(e.getId(), e.getRefundNo(), e.getPaymentId(), e.getPersonId(),
                e.getContractId(), e.getRefundAmount(), e.getRefundReason(), e.getRefundType(),
                e.getRefundChannel(), e.getRefundStatus(), st.label(), e.getApproveById(),
                e.getApproveTime(), e.getRefundTime(), e.getCreateTime());
    }
}
