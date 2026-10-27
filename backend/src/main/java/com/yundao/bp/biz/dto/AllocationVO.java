package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.AllocationStatus;
import com.yundao.bp.biz.entity.BizAllocation;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 配租单视图。
 */
public record AllocationVO(
        Long id,
        String allocationNo,
        Long batchId,
        Long personId,
        Long houseId,
        Long spaceId,
        String allocationType,
        LocalDate allocationDate,
        LocalDate planRentStart,
        LocalDate planRentEnd,
        String allocationStatus,
        String allocationStatusLabel,
        LocalDateTime lockExpireTime,
        /** 派生：距锁定到期的剩余小时（负数=已超时） */
        Long lockRemainHours,
        /** 派生：是否已超过锁定时间未签约 */
        Boolean lockOverdue,
        String giveUpReason,
        LocalDateTime createTime,
        String personName,
        String phoneMask
) {
    public static AllocationVO from(BizAllocation e) {
        if (e == null) {
            return null;
        }
        AllocationStatus st;
        try {
            st = AllocationStatus.valueOf(e.getAllocationStatus());
        } catch (IllegalArgumentException ex) {
            st = AllocationStatus.PENDING_SIGN;
        }
        Long remain = null;
        boolean overdue = false;
        if (e.getLockExpireTime() != null) {
            remain = ChronoUnit.HOURS.between(LocalDateTime.now(), e.getLockExpireTime());
            overdue = st.holdsHouse() && remain < 0;
        }
        return new AllocationVO(e.getId(), e.getAllocationNo(), e.getBatchId(), e.getPersonId(),
                e.getHouseId(), e.getSpaceId(), e.getAllocationType(), e.getAllocationDate(),
                e.getPlanRentStart(), e.getPlanRentEnd(), e.getAllocationStatus(), st.label(),
                e.getLockExpireTime(), remain, overdue, e.getGiveUpReason(), e.getCreateTime(),
                null, null);
    }

    /** 补充人员姓名与脱敏手机号 */
    public AllocationVO withPerson(String name, String phone) {
        return new AllocationVO(id, allocationNo, batchId, personId, houseId, spaceId,
                allocationType, allocationDate, planRentStart, planRentEnd, allocationStatus,
                allocationStatusLabel, lockExpireTime, lockRemainHours, lockOverdue,
                giveUpReason, createTime, name, phone);
    }
}
