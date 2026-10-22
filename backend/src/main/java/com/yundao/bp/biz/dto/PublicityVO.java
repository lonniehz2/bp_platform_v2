package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.PublicityStatus;
import com.yundao.bp.biz.constant.PublicityType;
import com.yundao.bp.biz.entity.BizPublicity;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 公示视图。
 */
public record PublicityVO(
        Long id,
        String publicityNo,
        String publicityType,
        String publicityTypeLabel,
        Long orgId,
        Long batchId,
        String title,
        String content,
        LocalDate startDate,
        LocalDate endDate,
        /** 公示天数 */
        Long durationDays,
        String attachmentUrl,
        String publicityStatus,
        String publicityStatusLabel,
        /** 派生：公示期是否已满（≥7 天且已到结束日） */
        Boolean periodMet,
        /** 派生：是否正在进行中 */
        Boolean ongoing,
        LocalDateTime createTime
) {
    public static PublicityVO from(BizPublicity e) {
        if (e == null) {
            return null;
        }
        PublicityStatus st;
        try {
            st = PublicityStatus.valueOf(e.getPublicityStatus());
        } catch (IllegalArgumentException ex) {
            st = PublicityStatus.DRAFT;
        }
        PublicityType tp;
        try {
            tp = PublicityType.valueOf(e.getPublicityType());
        } catch (IllegalArgumentException ex) {
            tp = PublicityType.QUALIFY;
        }
        long days = 0;
        if (e.getStartDate() != null && e.getEndDate() != null) {
            days = ChronoUnit.DAYS.between(e.getStartDate(), e.getEndDate()) + 1;
        }
        LocalDate today = LocalDate.now();
        boolean met = days >= 7 && e.getEndDate() != null && !today.isBefore(e.getEndDate());
        boolean ongoing = st == PublicityStatus.PUBLISHED && e.getStartDate() != null
                && e.getEndDate() != null
                && !today.isBefore(e.getStartDate()) && !today.isAfter(e.getEndDate());
        return new PublicityVO(e.getId(), e.getPublicityNo(), e.getPublicityType(), tp.label(),
                e.getOrgId(), e.getBatchId(), e.getTitle(), e.getContent(),
                e.getStartDate(), e.getEndDate(),
                days, e.getAttachmentUrl(), e.getPublicityStatus(), st.label(), met, ongoing,
                e.getCreateTime());
    }
}
