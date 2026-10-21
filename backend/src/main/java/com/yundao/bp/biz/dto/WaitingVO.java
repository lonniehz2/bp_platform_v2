package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.QueueStatus;
import com.yundao.bp.biz.entity.BizWaitingQueue;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 轮候记录视图。
 */
public record WaitingVO(
        Long id,
        String waitingNo,
        Long personId,
        Long applicationId,
        String securityType,
        Long orgId,
        Integer waitingRank,
        BigDecimal totalScore,
        BigDecimal priorityScore,
        /** 派生：实时轮候天数（按当前时间重算） */
        Integer liveWaitDays,
        LocalDateTime enterTime,
        LocalDate validUntil,
        String queueStatus,
        String queueStatusLabel,
        String freezeReason,
        Boolean expired
) {
    public static WaitingVO from(BizWaitingQueue e) {
        if (e == null) {
            return null;
        }
        QueueStatus st;
        try {
            st = QueueStatus.valueOf(e.getQueueStatus());
        } catch (IllegalArgumentException ex) {
            st = QueueStatus.WAITING;
        }
        int live = e.getEnterTime() == null ? 0
                : (int) ChronoUnit.DAYS.between(e.getEnterTime().toLocalDate(), LocalDate.now());
        boolean exp = e.getValidUntil() != null && e.getValidUntil().isBefore(LocalDate.now());
        return new WaitingVO(e.getId(), e.getWaitingNo(), e.getPersonId(), e.getApplicationId(),
                e.getSecurityType(), e.getOrgId(), e.getWaitingRank(), e.getTotalScore(),
                e.getPriorityScore(), live, e.getEnterTime(), e.getValidUntil(),
                e.getQueueStatus(), st.label(), e.getFreezeReason(), exp);
    }
}
