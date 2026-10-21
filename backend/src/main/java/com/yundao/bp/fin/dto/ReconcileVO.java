package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.ReconcileStatus;
import com.yundao.bp.fin.entity.FinReconcile;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 对账记录视图。
 */
public record ReconcileVO(
        Long id,
        String reconcileNo,
        LocalDate reconcileDate,
        String reconcileType,
        String payChannel,
        BigDecimal systemAmount,
        BigDecimal channelAmount,
        BigDecimal diffAmount,
        Integer diffCount,
        String reconcileStatus,
        String reconcileStatusLabel,
        /** 派生：是否账实相符 */
        Boolean matched,
        String diffDetailUrl,
        LocalDateTime createTime
) {
    public static ReconcileVO from(FinReconcile e) {
        if (e == null) {
            return null;
        }
        ReconcileStatus st;
        try {
            st = ReconcileStatus.valueOf(e.getReconcileStatus());
        } catch (IllegalArgumentException ex) {
            st = ReconcileStatus.DIFF;
        }
        BigDecimal diff = e.getDiffAmount() == null ? BigDecimal.ZERO : e.getDiffAmount();
        return new ReconcileVO(e.getId(), e.getReconcileNo(), e.getReconcileDate(),
                e.getReconcileType(), e.getPayChannel(), e.getSystemAmount(),
                e.getChannelAmount(), e.getDiffAmount(), e.getDiffCount(),
                e.getReconcileStatus(), st.label(), diff.compareTo(BigDecimal.ZERO) == 0,
                e.getDiffDetailUrl(), e.getCreateTime());
    }
}
