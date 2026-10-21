package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ApproveStatus;
import com.yundao.bp.biz.constant.ChangeType;
import com.yundao.bp.biz.entity.BizContractChange;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 合同变更视图。
 */
public record ChangeVO(
        Long id,
        Long contractId,
        Long newContractId,
        String changeType,
        String changeTypeLabel,
        String changeReason,
        String beforeJson,
        String afterJson,
        String approveStatus,
        String approveStatusLabel,
        LocalDate effectiveDate,
        LocalDateTime createTime
) {
    public static ChangeVO from(BizContractChange e) {
        if (e == null) {
            return null;
        }
        ChangeType ct;
        try {
            ct = ChangeType.valueOf(e.getChangeType());
        } catch (IllegalArgumentException ex) {
            ct = ChangeType.OTHER;
        }
        ApproveStatus st;
        try {
            st = ApproveStatus.valueOf(e.getApproveStatus());
        } catch (IllegalArgumentException ex) {
            st = ApproveStatus.PENDING;
        }
        return new ChangeVO(e.getId(), e.getContractId(), e.getNewContractId(),
                e.getChangeType(), ct.label(), e.getChangeReason(), e.getBeforeJson(),
                e.getAfterJson(), e.getApproveStatus(), st.label(), e.getEffectiveDate(),
                e.getCreateTime());
    }
}
