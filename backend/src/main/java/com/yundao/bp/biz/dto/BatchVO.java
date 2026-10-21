package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.BatchStatus;
import com.yundao.bp.biz.entity.BizBatch;
import java.time.LocalDateTime;

/**
 * 配租批次视图。
 */
public record BatchVO(
        Long id,
        String batchNo,
        String batchName,
        Long orgId,
        String securityType,
        String batchType,
        Integer houseCount,
        Integer applicantCount,
        LocalDateTime signupStart,
        LocalDateTime signupEnd,
        LocalDateTime lotteryTime,
        LocalDateTime selectStart,
        LocalDateTime selectEnd,
        String lotterySeed,
        String notaryInfo,
        String batchStatus,
        String batchStatusLabel,
        String remark,
        LocalDateTime createTime
) {
    public static BatchVO from(BizBatch e) {
        if (e == null) {
            return null;
        }
        BatchStatus st;
        try {
            st = BatchStatus.valueOf(e.getBatchStatus());
        } catch (IllegalArgumentException ex) {
            st = BatchStatus.DRAFT;
        }
        return new BatchVO(e.getId(), e.getBatchNo(), e.getBatchName(), e.getOrgId(),
                e.getSecurityType(), e.getBatchType(), e.getHouseCount(), e.getApplicantCount(),
                e.getSignupStart(), e.getSignupEnd(), e.getLotteryTime(), e.getSelectStart(),
                e.getSelectEnd(), e.getLotterySeed(), e.getNotaryInfo(), e.getBatchStatus(),
                st.label(), e.getRemark(), e.getCreateTime());
    }
}
