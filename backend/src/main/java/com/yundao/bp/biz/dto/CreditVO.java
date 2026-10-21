package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.CreditStatus;
import com.yundao.bp.biz.constant.SanctionType;
import com.yundao.bp.biz.constant.ViolationType;
import com.yundao.bp.biz.entity.BizCreditRecord;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 信用惩戒记录视图。
 */
public record CreditVO(
        Long id,
        String recordNo,
        Long personId,
        String bizType,
        Long bizId,
        String violationType,
        String violationTypeLabel,
        String violationDesc,
        String evidenceUrl,
        String sanctionType,
        String sanctionTypeLabel,
        Integer banYears,
        LocalDate banStartDate,
        LocalDate banEndDate,
        /** 派生：当前是否处于限制申请期内 */
        Boolean underBan,
        String pushPlatform,
        String pushStatus,
        Boolean pushed,
        LocalDateTime pushTime,
        Long decideOrgId,
        Long decideUserId,
        LocalDateTime decideTime,
        String legalDocNo,
        String status,
        String statusLabel,
        String remark,
        LocalDateTime createTime
) {
    public static CreditVO from(BizCreditRecord e) {
        if (e == null) {
            return null;
        }
        CreditStatus st;
        try {
            st = CreditStatus.valueOf(e.getStatus());
        } catch (IllegalArgumentException ex) {
            st = CreditStatus.EFFECTIVE;
        }
        ViolationType vt;
        try {
            vt = ViolationType.valueOf(e.getViolationType());
        } catch (IllegalArgumentException ex) {
            vt = ViolationType.OTHER;
        }
        SanctionType sa;
        try {
            sa = SanctionType.valueOf(e.getSanctionType());
        } catch (IllegalArgumentException ex) {
            sa = SanctionType.OTHER;
        }
        LocalDate today = LocalDate.now();
        boolean underBan = st == CreditStatus.EFFECTIVE
                && e.getBanEndDate() != null
                && !today.isAfter(e.getBanEndDate())
                && (e.getBanStartDate() == null || !today.isBefore(e.getBanStartDate()));
        return new CreditVO(e.getId(), e.getRecordNo(), e.getPersonId(), e.getBizType(),
                e.getBizId(), e.getViolationType(), vt.label(), e.getViolationDesc(),
                e.getEvidenceUrl(), e.getSanctionType(), sa.label(), e.getBanYears(),
                e.getBanStartDate(), e.getBanEndDate(), underBan, e.getPushPlatform(),
                e.getPushStatus(), "PUSHED".equals(e.getPushStatus()), e.getPushTime(),
                e.getDecideOrgId(), e.getDecideUserId(), e.getDecideTime(), e.getLegalDocNo(),
                e.getStatus(), st.label(), e.getRemark(), e.getCreateTime());
    }
}
