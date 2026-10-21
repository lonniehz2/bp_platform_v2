package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.DunningType;
import com.yundao.bp.fin.entity.FinDunningRecord;
import java.time.LocalDateTime;

/**
 * 催缴记录视图。
 */
public record DunningVO(
        Long id,
        Long billId,
        Long personId,
        Integer dunningNo,
        String dunningType,
        String dunningTypeLabel,
        LocalDateTime dunningTime,
        String dunningContent,
        String dunningResult,
        String evidenceUrl,
        Long operatorId,
        LocalDateTime createTime
) {
    public static DunningVO from(FinDunningRecord e) {
        if (e == null) {
            return null;
        }
        DunningType t;
        try {
            t = DunningType.valueOf(e.getDunningType());
        } catch (IllegalArgumentException ex) {
            t = DunningType.SMS;
        }
        return new DunningVO(e.getId(), e.getBillId(), e.getPersonId(), e.getDunningNo(),
                e.getDunningType(), t.label(), e.getDunningTime(), e.getDunningContent(),
                e.getDunningResult(), e.getEvidenceUrl(), e.getOperatorId(), e.getCreateTime());
    }
}
