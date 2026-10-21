package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.AppealBizType;
import com.yundao.bp.biz.constant.AppealResultEffect;
import com.yundao.bp.biz.constant.AppealStatus;
import com.yundao.bp.biz.entity.BizAppeal;
import java.time.LocalDateTime;

/**
 * 申诉/异议视图。
 */
public record AppealVO(
        Long id,
        String appealNo,
        String bizType,
        String bizTypeLabel,
        Long bizId,
        Long personId,
        Long orgId,
        String appealType,
        String appealReason,
        String appealEvidence,
        LocalDateTime deadlineTime,
        LocalDateTime appealTime,
        /** 派生：是否已超申诉期限 */
        Boolean overdue,
        LocalDateTime acceptTime,
        Long acceptUserId,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        String reviewOpinion,
        String appealStatus,
        String appealStatusLabel,
        String resultEffect,
        String resultEffectLabel,
        Boolean changesOutcome,
        String notifyStatus,
        Boolean notified,
        LocalDateTime createTime
) {
    public static AppealVO from(BizAppeal e) {
        if (e == null) {
            return null;
        }
        AppealStatus st;
        try {
            st = AppealStatus.valueOf(e.getAppealStatus());
        } catch (IllegalArgumentException ex) {
            st = AppealStatus.SUBMITTED;
        }
        AppealBizType bt;
        try {
            bt = AppealBizType.valueOf(e.getBizType());
        } catch (IllegalArgumentException ex) {
            bt = AppealBizType.APPLICATION;
        }
        AppealResultEffect re = null;
        if (e.getResultEffect() != null && !e.getResultEffect().isBlank()) {
            try {
                re = AppealResultEffect.valueOf(e.getResultEffect());
            } catch (IllegalArgumentException ignored) {
                re = AppealResultEffect.NONE;
            }
        }
        boolean overdue = e.getDeadlineTime() != null
                && LocalDateTime.now().isAfter(e.getDeadlineTime())
                && st == AppealStatus.TIMEOUT;
        return new AppealVO(e.getId(), e.getAppealNo(), e.getBizType(), bt.label(), e.getBizId(),
                e.getPersonId(), e.getOrgId(), e.getAppealType(), e.getAppealReason(),
                e.getAppealEvidence(), e.getDeadlineTime(), e.getAppealTime(), overdue,
                e.getAcceptTime(), e.getAcceptUserId(), e.getHandleUserId(), e.getHandleTime(),
                e.getHandleResult(), e.getReviewOpinion(), e.getAppealStatus(), st.label(),
                e.getResultEffect(), re == null ? null : re.label(),
                re != null && re.changesOutcome(), e.getNotifyStatus(),
                "SENT".equals(e.getNotifyStatus()), e.getCreateTime());
    }
}
