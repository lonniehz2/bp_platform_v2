package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.SettleStatus;
import com.yundao.bp.biz.constant.TerminationStatus;
import com.yundao.bp.biz.entity.BizTermination;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 退租单视图（含"能否办结"的派生判定）。
 */
public record TerminationVO(
        Long id,
        String terminationNo,
        Long contractId,
        Long houseId,
        Long personId,
        String terminationType,
        LocalDateTime applyTime,
        LocalDate planExitDate,
        LocalDate actualExitDate,
        String exitReason,
        String inspectStatus,
        String inspectResult,
        BigDecimal damageAmount,
        BigDecimal settleAmount,
        BigDecimal depositRefund,
        BigDecimal arrearsAmount,
        String settleStatus,
        String settleStatusLabel,
        String terminationStatus,
        String terminationStatusLabel,
        Boolean houseReleased,
        Boolean grantRevoked,
        LocalDate transitionStartDate,
        LocalDate transitionEndDate,
        Integer transitionMonths,
        BigDecimal transitionRentMultiplier,
        LocalDate relocationStartDate,
        LocalDate relocationEndDate,
        Boolean enforceFlag,
        String enforceCourt,
        String itemHandlerName,
        Boolean notaryFlag,
        String notaryNo,
        LocalDate banReapplyEndDate,
        /** 派生：四个前置是否齐备（验房通过 + 结算完成 + 房源已释放 + 授权已回收） */
        Boolean readyToComplete,
        /** 派生：是否逾期未退房（计划退房日已过仍无实际退房日） */
        Boolean overdueExit,
        LocalDateTime createTime
) {
    public static TerminationVO from(BizTermination e) {
        if (e == null) {
            return null;
        }
        TerminationStatus st;
        try {
            st = TerminationStatus.valueOf(e.getTerminationStatus());
        } catch (IllegalArgumentException ex) {
            st = TerminationStatus.APPLYING;
        }
        SettleStatus settle;
        try {
            settle = SettleStatus.valueOf(
                    e.getSettleStatus() == null ? "PENDING" : e.getSettleStatus());
        } catch (IllegalArgumentException ex) {
            settle = SettleStatus.PENDING;
        }
        boolean inspectOk = "PASSED".equals(e.getInspectStatus());
        boolean settleOk = settle == SettleStatus.SETTLED || settle == SettleStatus.WAIVED;
        boolean released = e.getHouseReleased() != null && e.getHouseReleased() == 1;
        boolean revoked = e.getGrantRevoked() != null && e.getGrantRevoked() == 1;
        boolean ready = inspectOk && settleOk && released && revoked;
        boolean overdue = e.getPlanExitDate() != null && e.getActualExitDate() == null
                && LocalDate.now().isAfter(e.getPlanExitDate())
                && !st.isTerminal();
        return new TerminationVO(e.getId(), e.getTerminationNo(), e.getContractId(),
                e.getHouseId(), e.getPersonId(), e.getTerminationType(), e.getApplyTime(),
                e.getPlanExitDate(), e.getActualExitDate(), e.getExitReason(),
                e.getInspectStatus(), e.getInspectResult(), e.getDamageAmount(),
                e.getSettleAmount(), e.getDepositRefund(), e.getArrearsAmount(),
                e.getSettleStatus(), settle.label(), e.getTerminationStatus(), st.label(),
                released, revoked, e.getTransitionStartDate(), e.getTransitionEndDate(),
                e.getTransitionMonths(), e.getTransitionRentMultiplier(),
                e.getRelocationStartDate(), e.getRelocationEndDate(),
                e.getEnforceFlag() != null && e.getEnforceFlag() == 1,
                e.getEnforceCourt(), e.getItemHandlerName(),
                e.getNotaryFlag() != null && e.getNotaryFlag() == 1, e.getNotaryNo(),
                e.getBanReapplyEndDate(), ready, overdue, e.getCreateTime());
    }
}
