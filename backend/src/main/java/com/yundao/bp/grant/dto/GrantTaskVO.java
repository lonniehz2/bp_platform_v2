package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.entity.GrantTask;
import java.time.LocalDateTime;

/**
 * 授权任务视图。
 */
public record GrantTaskVO(
        Long id,
        String taskNo,
        String taskType,
        Long personId,
        Long entitlementId,
        Integer lockCount,
        Integer successCount,
        Integer failCount,
        String iotTaskId,
        String taskStatus,
        String taskStatusLabel,
        Integer retryCount,
        String lastError,
        String triggerSource,
        LocalDateTime dispatchTime,
        LocalDateTime finishTime,
        LocalDateTime createTime
) {
    public static GrantTaskVO from(GrantTask t) {
        if (t == null) {
            return null;
        }
        GrantTaskStatus st;
        try {
            st = GrantTaskStatus.valueOf(t.getTaskStatus());
        } catch (IllegalArgumentException ex) {
            st = GrantTaskStatus.PENDING;
        }
        return new GrantTaskVO(t.getId(), t.getTaskNo(), t.getTaskType(), t.getPersonId(),
                t.getEntitlementId(), t.getLockCount(), t.getSuccessCount(), t.getFailCount(),
                t.getIotTaskId(), t.getTaskStatus(), st.label(), t.getRetryCount(),
                t.getLastError(), t.getTriggerSource(), t.getDispatchTime(), t.getFinishTime(),
                t.getCreateTime());
    }
}
