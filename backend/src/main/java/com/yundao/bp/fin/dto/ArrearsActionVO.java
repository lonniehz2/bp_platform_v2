package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.ArrearsActionStatus;
import com.yundao.bp.fin.constant.FreezeScope;
import com.yundao.bp.fin.entity.FinArrearsAction;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 欠费处置单视图。
 */
public record ArrearsActionVO(
        Long id,
        String actionNo,
        Long contractId,
        Long personId,
        BigDecimal arrearsAmount,
        Integer overdueDays,
        String triggerType,
        String actionType,
        String freezeScope,
        String freezeScopeLabel,
        /** 是否停用了大门（安全底线被突破，应为 false） */
        Boolean freezesMainDoor,
        String actionStatus,
        String actionStatusLabel,
        LocalDateTime executeTime,
        Long grantTaskId,
        String revokeReason,
        LocalDateTime createTime
) {
    public static ArrearsActionVO from(FinArrearsAction e) {
        if (e == null) {
            return null;
        }
        ArrearsActionStatus st;
        try {
            st = ArrearsActionStatus.valueOf(e.getActionStatus());
        } catch (IllegalArgumentException ex) {
            st = ArrearsActionStatus.PENDING;
        }
        FreezeScope scope;
        try {
            scope = e.getFreezeScope() == null ? FreezeScope.EXCLUDE_MAIN_DOOR
                    : FreezeScope.valueOf(e.getFreezeScope());
        } catch (IllegalArgumentException ex) {
            scope = FreezeScope.EXCLUDE_MAIN_DOOR;
        }
        return new ArrearsActionVO(e.getId(), e.getActionNo(), e.getContractId(),
                e.getPersonId(), e.getArrearsAmount(), e.getOverdueDays(),
                e.getTriggerType(), e.getActionType(), e.getFreezeScope(), scope.label(),
                scope == FreezeScope.ALL, e.getActionStatus(), st.label(),
                e.getExecuteTime(), e.getGrantTaskId(), e.getRevokeReason(), e.getCreateTime());
    }
}
