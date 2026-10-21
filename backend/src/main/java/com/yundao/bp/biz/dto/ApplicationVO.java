package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ApplicationStatus;
import com.yundao.bp.biz.entity.BizApplication;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 申请单视图。
 */
public record ApplicationVO(
        Long id,
        String applicationNo,
        Long orgId,
        Long personId,
        /** 申请人姓名（列表展示用，批量查询填充，避免前端显示 ID） */
        String personName,
        String securityType,
        String securityMode,
        String applyChannel,
        LocalDateTime applyTime,
        Integer familySize,
        String intentDistrict,
        String intentLayout,
        String applicationStatus,
        String applicationStatusLabel,
        String currentNode,
        String rejectReason,
        String supplementDemand,
        BigDecimal declaredIncome,
        BigDecimal incomePerCapita,
        Integer complianceCommitFlag,
        Integer dataShareAgreeFlag,
        LocalDateTime acceptTime,
        String remark,
        LocalDateTime createTime
) {
    public static ApplicationVO from(BizApplication e) {
        return from(e, null);
    }

    public static ApplicationVO from(BizApplication e, String personName) {
        if (e == null) {
            return null;
        }
        ApplicationStatus st;
        try {
            st = ApplicationStatus.valueOf(e.getApplicationStatus());
        } catch (IllegalArgumentException ex) {
            st = ApplicationStatus.DRAFT;
        }
        return new ApplicationVO(e.getId(), e.getApplicationNo(), e.getOrgId(),
                e.getPersonId(),
                personName, e.getSecurityType(), e.getSecurityMode(), e.getApplyChannel(),
                e.getApplyTime(), e.getFamilySize(), e.getIntentDistrict(), e.getIntentLayout(),
                e.getApplicationStatus(), st.label(), e.getCurrentNode(), e.getRejectReason(),
                e.getSupplementDemand(), e.getDeclaredIncome(), e.getIncomePerCapita(),
                e.getComplianceCommitFlag(), e.getDataShareAgreeFlag(), e.getAcceptTime(),
                e.getRemark(), e.getCreateTime());
    }
}
