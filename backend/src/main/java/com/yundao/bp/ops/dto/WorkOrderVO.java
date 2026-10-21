package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.WorkOrderStatus;
import com.yundao.bp.ops.entity.OpsWorkorder;
import java.time.LocalDateTime;

/**
 * 工单视图（含派生指标）。
 */
public record WorkOrderVO(
        Long id,
        String workorderNo,
        String orderType,
        String orderSource,
        String orderTitle,
        String orderContent,
        String orderAddress,
        Long orgId,
        Long spaceId,
        Long houseId,
        String deviceId,
        Long personId,
        String reporterName,
        String reporterPhone,
        Long assignUserId,
        String assignUserName,
        String orderStatus,
        String orderStatusLabel,
        String slaStatus,
        /** 响应时限（分钟）—— 前端据此算"剩余 X 分钟" */
        Integer slaResponseMinutes,
        /** 完工时限（分钟） */
        Integer slaFinishMinutes,
        /** 派生：是否已超响应时限（未接单且已超时） */
        Boolean responseOverdue,
        /** 派生：是否已超完工时限（未完工且已超时） */
        Boolean finishOverdue,
        LocalDateTime assignTime,
        LocalDateTime acceptTime,
        LocalDateTime finishTime,
        LocalDateTime closeTime,
        String handleResult,
        Integer evaluateScore,
        LocalDateTime createTime
) {
    public static WorkOrderVO from(OpsWorkorder e) {
        if (e == null) {
            return null;
        }
        WorkOrderStatus st;
        try {
            st = WorkOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            st = WorkOrderStatus.PENDING;
        }
        LocalDateTime now = LocalDateTime.now();
        boolean responseOverdue = false;
        if (e.getAcceptTime() == null && e.getSlaResponseMinutes() != null
                && e.getCreateTime() != null && st.isOpen()) {
            responseOverdue = now.isAfter(
                    e.getCreateTime().plusMinutes(e.getSlaResponseMinutes()));
        }
        boolean finishOverdue = false;
        if (e.getFinishTime() == null && e.getSlaFinishMinutes() != null
                && e.getCreateTime() != null && st.isOpen()) {
            finishOverdue = now.isAfter(
                    e.getCreateTime().plusMinutes(e.getSlaFinishMinutes()));
        }
        return new WorkOrderVO(e.getId(), e.getWorkorderNo(), e.getOrderType(),
                e.getOrderSource(), e.getOrderTitle(), e.getOrderContent(), e.getOrderAddress(),
                e.getOrgId(), e.getSpaceId(), e.getHouseId(), e.getDeviceId(), e.getPersonId(),
                e.getReporterName(), e.getReporterPhone(), e.getAssignUserId(),
                e.getAssignUserName(), e.getOrderStatus(), st.label(), e.getSlaStatus(),
                e.getSlaResponseMinutes(), e.getSlaFinishMinutes(),
                responseOverdue, finishOverdue, e.getAssignTime(), e.getAcceptTime(),
                e.getFinishTime(), e.getCloseTime(), e.getHandleResult(), e.getEvaluateScore(),
                e.getCreateTime());
    }
}
