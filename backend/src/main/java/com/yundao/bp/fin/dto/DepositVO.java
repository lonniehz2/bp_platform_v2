package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.DepositStatus;
import com.yundao.bp.fin.entity.FinDeposit;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 押金台账视图。
 */
public record DepositVO(
        Long id,
        Long contractId,
        Long personId,
        BigDecimal depositAmount,
        BigDecimal paidAmount,
        BigDecimal deductAmount,
        BigDecimal refundAmount,
        BigDecimal balanceAmount,
        String depositStatus,
        String depositStatusLabel,
        BigDecimal capAmount,
        Boolean exempt,
        String exemptReason,
        /** 是否超政策上限（成都 1000 元） */
        Boolean overCap,
        /** 派生：尚欠收押金 = 应收 - 已收 */
        BigDecimal unpaidAmount,
        LocalDateTime createTime
) {
    public static DepositVO from(FinDeposit e) {
        if (e == null) {
            return null;
        }
        DepositStatus st;
        try {
            st = DepositStatus.valueOf(e.getDepositStatus());
        } catch (IllegalArgumentException ex) {
            st = DepositStatus.HELD;
        }
        BigDecimal due = e.getDepositAmount() == null ? BigDecimal.ZERO : e.getDepositAmount();
        BigDecimal paid = e.getPaidAmount() == null ? BigDecimal.ZERO : e.getPaidAmount();
        return new DepositVO(e.getId(), e.getContractId(), e.getPersonId(), e.getDepositAmount(),
                e.getPaidAmount(), e.getDeductAmount(), e.getRefundAmount(), e.getBalanceAmount(),
                e.getDepositStatus(), st.label(), e.getCapAmount(),
                e.getIsExempt() != null && e.getIsExempt() == 1, e.getExemptReason(),
                e.getOverCapFlag() != null && e.getOverCapFlag() == 1,
                due.subtract(paid), e.getCreateTime());
    }
}
