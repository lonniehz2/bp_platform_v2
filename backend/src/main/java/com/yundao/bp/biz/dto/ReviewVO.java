package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.AnnualReviewResult;
import com.yundao.bp.biz.constant.ReviewStatus;
import com.yundao.bp.biz.entity.BizAnnualReview;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 年审（复核）视图。
 */
public record ReviewVO(
        Long id,
        String reviewNo,
        Long personId,
        Long contractId,
        Long houseId,
        String reviewYear,
        String reviewBatch,
        String reviewType,
        String triggerReason,
        String checkResult,
        String reviewResult,
        String reviewResultLabel,
        String adjustContent,
        String reviewStatus,
        String reviewStatusLabel,
        LocalDate reviewDate,
        LocalDate nextReviewDate,
        Long reviewUserId,
        LocalDateTime createTime
) {
    public static ReviewVO from(BizAnnualReview e) {
        if (e == null) {
            return null;
        }
        ReviewStatus st;
        try {
            st = ReviewStatus.valueOf(e.getReviewStatus());
        } catch (IllegalArgumentException ex) {
            st = ReviewStatus.PENDING;
        }
        String rl = null;
        if (e.getReviewResult() != null && !e.getReviewResult().isBlank()) {
            try {
                rl = AnnualReviewResult.valueOf(e.getReviewResult()).label();
            } catch (IllegalArgumentException ex) {
                rl = e.getReviewResult();
            }
        }
        return new ReviewVO(e.getId(), e.getReviewNo(), e.getPersonId(), e.getContractId(),
                e.getHouseId(), e.getReviewYear(), e.getReviewBatch(), e.getReviewType(),
                e.getTriggerReason(), e.getCheckResult(), e.getReviewResult(), rl,
                e.getAdjustContent(), e.getReviewStatus(), st.label(), e.getReviewDate(),
                e.getNextReviewDate(), e.getReviewUserId(), e.getCreateTime());
    }
}
