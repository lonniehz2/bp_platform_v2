package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.FlowType;
import com.yundao.bp.fin.constant.VerifyStatus;
import com.yundao.bp.fin.entity.FinCashFlow;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 资金流水视图。
 */
public record CashFlowVO(
        Long id,
        String flowNo,
        String flowType,
        String flowTypeLabel,
        String bizType,
        Long bizId,
        BigDecimal amount,
        BigDecimal balanceAfter,
        LocalDateTime flowTime,
        String verifyStatus,
        String verifyStatusLabel,
        String verifyRemark,
        LocalDateTime createTime
) {
    public static CashFlowVO from(FinCashFlow e) {
        if (e == null) {
            return null;
        }
        FlowType ft;
        try {
            ft = FlowType.valueOf(e.getFlowType());
        } catch (IllegalArgumentException ex) {
            ft = FlowType.INCOME;
        }
        VerifyStatus vs;
        try {
            vs = VerifyStatus.valueOf(e.getVerifyStatus());
        } catch (IllegalArgumentException ex) {
            vs = VerifyStatus.UNVERIFIED;
        }
        return new CashFlowVO(e.getId(), e.getFlowNo(), e.getFlowType(), ft.label(),
                e.getBizType(), e.getBizId(), e.getAmount(), e.getBalanceAfter(),
                e.getFlowTime(), e.getVerifyStatus(), vs.label(), e.getVerifyRemark(),
                e.getCreateTime());
    }
}
