package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.PayStatus;
import com.yundao.bp.fin.entity.FinPayment;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 收款单视图（含"可核销余额"派生）。
 */
public record PaymentVO(
        Long id,
        String paymentNo,
        Long orgId,
        Long personId,
        String payerName,
        BigDecimal payAmount,
        String payChannel,
        LocalDateTime payTime,
        String tradeNo,
        String payStatus,
        String payStatusLabel,
        String reconcileStatus,
        BigDecimal reconciledAmount,
        /** 派生：可核销余额 = 收款金额 - 已核销 */
        BigDecimal remainAmount,
        Boolean unknownFlag,
        String remark,
        LocalDateTime createTime
) {
    public static PaymentVO from(FinPayment e) {
        if (e == null) {
            return null;
        }
        PayStatus st;
        try {
            st = PayStatus.valueOf(e.getPayStatus());
        } catch (IllegalArgumentException ex) {
            st = PayStatus.PENDING;
        }
        BigDecimal paid = e.getPayAmount() == null ? BigDecimal.ZERO : e.getPayAmount();
        BigDecimal done = e.getReconciledAmount() == null ? BigDecimal.ZERO : e.getReconciledAmount();
        return new PaymentVO(e.getId(), e.getPaymentNo(), e.getOrgId(), e.getPersonId(),
                e.getPayerName(), e.getPayAmount(), e.getPayChannel(), e.getPayTime(),
                e.getTradeNo(), e.getPayStatus(), st.label(), e.getReconcileStatus(),
                e.getReconciledAmount(), paid.subtract(done), 
                e.getUnknownFlag() != null && e.getUnknownFlag() == 1,
                e.getRemark(), e.getCreateTime());
    }
}
