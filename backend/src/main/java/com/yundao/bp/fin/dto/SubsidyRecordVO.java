package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.SubsidyStatus;
import com.yundao.bp.fin.entity.FinSubsidyRecord;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 补贴发放记录视图。
 */
public record SubsidyRecordVO(
        Long id,
        String recordNo,
        Long standardId,
        Long contractId,
        Long personId,
        String personName,
        Long orgId,
        String subsidyPeriod,
        BigDecimal subsidyAmount,
        BigDecimal paidAmount,
        String payMode,
        String recordStatus,
        String recordStatusLabel,
        String financeBatchNo,
        String failReason,
        LocalDate issueDate,
        LocalDateTime createTime
) {
    public static SubsidyRecordVO from(FinSubsidyRecord e) {
        if (e == null) {
            return null;
        }
        SubsidyStatus st;
        try {
            st = SubsidyStatus.valueOf(e.getRecordStatus());
        } catch (IllegalArgumentException ex) {
            st = SubsidyStatus.PENDING;
        }
        return new SubsidyRecordVO(e.getId(), e.getRecordNo(), e.getStandardId(),
                e.getContractId(), e.getPersonId(), e.getPersonName(), e.getOrgId(),
                e.getSubsidyPeriod(), e.getSubsidyAmount(), e.getPaidAmount(), e.getPayMode(),
                e.getRecordStatus(), st.label(), e.getFinanceBatchNo(), e.getFailReason(),
                e.getIssueDate(), e.getCreateTime());
    }
}
