package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.GrantStatus;
import com.yundao.bp.grant.entity.GrantEntitlement;
import java.time.LocalDateTime;

/**
 * 权益视图。
 */
public record GrantVO(
        Long id,
        String grantNo,
        Long personId,
        Long spaceId,
        Long houseId,
        String grantLevel,
        LocalDateTime validStart,
        LocalDateTime validEnd,
        Boolean allowOpen,
        Integer visitLimitTimes,
        Integer visitUsedTimes,
        String grantStatus,
        String grantStatusLabel,
        String sourceType,
        Long sourceId,
        String remark,
        LocalDateTime createTime
) {
    public static GrantVO from(GrantEntitlement e) {
        if (e == null) {
            return null;
        }
        GrantStatus st;
        try {
            st = GrantStatus.valueOf(e.getGrantStatus());
        } catch (IllegalArgumentException ex) {
            st = GrantStatus.PENDING;
        }
        return new GrantVO(e.getId(), e.getGrantNo(), e.getPersonId(), e.getSpaceId(),
                e.getHouseId(), e.getGrantLevel(), e.getValidStart(), e.getValidEnd(),
                e.getAllowOpen() != null && e.getAllowOpen() == 1,
                e.getVisitLimitTimes(), e.getVisitUsedTimes(),
                e.getGrantStatus(), st.label(), e.getSourceType(), e.getSourceId(),
                e.getRemark(), e.getCreateTime());
    }
}
