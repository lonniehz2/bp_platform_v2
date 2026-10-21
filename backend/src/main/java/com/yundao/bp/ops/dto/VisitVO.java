package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.MatchResult;
import com.yundao.bp.ops.constant.VisitStatus;
import com.yundao.bp.ops.entity.OpsHouseVisit;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 走访视图。
 */
public record VisitVO(
        Long id,
        String visitNo,
        String visitType,
        Long orgId,
        Long houseId,
        Long spaceId,
        Long personId,
        LocalDate planDate,
        LocalDate actualDate,
        Long visitUserId,
        String visitUserName,
        String triggerReason,
        Long alertId,
        Boolean occupied,
        Integer actualResidents,
        String matchResult,
        String matchResultLabel,
        String findings,
        Boolean sublease,
        Boolean idle,
        Boolean illegalUse,
        String images,
        String location,
        String visitStatus,
        String visitStatusLabel,
        String nextAction,
        Long workorderId,
        /** 派生：是否逾期未走访（计划日期已过但仍 PENDING） */
        Boolean overdue,
        LocalDateTime createTime
) {
    public static VisitVO from(OpsHouseVisit e) {
        if (e == null) {
            return null;
        }
        VisitStatus st;
        try {
            st = VisitStatus.valueOf(e.getVisitStatus());
        } catch (IllegalArgumentException ex) {
            st = VisitStatus.PENDING;
        }
        String mr = e.getMatchResult();
        String mrLabel = mr == null ? null : switch (mr) {
            case "MATCH" -> "一致";
            case "MISMATCH" -> "不一致";
            case "UNKNOWN" -> "无法确认";
            default -> mr;
        };
        boolean overdue = st == VisitStatus.PENDING && e.getPlanDate() != null
                && LocalDate.now().isAfter(e.getPlanDate());
        return new VisitVO(e.getId(), e.getVisitNo(), e.getVisitType(), e.getOrgId(),
                e.getHouseId(), e.getSpaceId(), e.getPersonId(), e.getPlanDate(),
                e.getActualDate(), e.getVisitUserId(), e.getVisitUserName(),
                e.getTriggerReason(), e.getAlertId(),
                e.getIsOccupied() != null && e.getIsOccupied() == 1,
                e.getActualResidents(), mr, mrLabel, e.getFindings(),
                e.getIsSublease() != null && e.getIsSublease() == 1,
                e.getIsIdle() != null && e.getIsIdle() == 1,
                e.getIsIllegalUse() != null && e.getIsIllegalUse() == 1,
                e.getImages(), e.getLocation(), e.getVisitStatus(), st.label(),
                e.getNextAction(), e.getWorkorderId(), overdue, e.getCreateTime());
    }
}
