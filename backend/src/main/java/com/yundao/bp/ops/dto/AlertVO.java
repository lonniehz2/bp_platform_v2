package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.AlertStatus;
import com.yundao.bp.ops.entity.OpsAlert;
import java.time.LocalDateTime;

/**
 * 告警视图。
 */
public record AlertVO(
        Long id,
        String alertNo,
        String alertCategory,
        String alertType,
        String alertLevel,
        String alertLevelLabel,
        String alertTitle,
        String alertContent,
        String alertValue,
        String thresholdValue,
        Long orgId,
        Long spaceId,
        Long houseId,
        Long personId,
        String deviceId,
        String alertStatus,
        String alertStatusLabel,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        Long workorderId,
        LocalDateTime alertTime,
        LocalDateTime createTime
) {
    public static AlertVO from(OpsAlert e) {
        if (e == null) {
            return null;
        }
        AlertStatus st;
        try {
            st = AlertStatus.valueOf(e.getAlertStatus());
        } catch (IllegalArgumentException ex) {
            st = AlertStatus.PENDING;
        }
        String levelLabel = switch (e.getAlertLevel() == null ? "" : e.getAlertLevel()) {
            case "URGENT" -> "紧急";
            case "IMPORTANT" -> "重要";
            case "NORMAL" -> "一般";
            default -> e.getAlertLevel();
        };
        return new AlertVO(e.getId(), e.getAlertNo(), e.getAlertCategory(), e.getAlertType(),
                e.getAlertLevel(), levelLabel, e.getAlertTitle(), e.getAlertContent(),
                e.getAlertValue(), e.getThresholdValue(), e.getOrgId(), e.getSpaceId(),
                e.getHouseId(), e.getPersonId(), e.getDeviceId(), e.getAlertStatus(),
                st.label(), e.getHandleUserId(), e.getHandleTime(), e.getHandleResult(),
                e.getWorkorderId(), e.getAlertTime(), e.getCreateTime());
    }
}
