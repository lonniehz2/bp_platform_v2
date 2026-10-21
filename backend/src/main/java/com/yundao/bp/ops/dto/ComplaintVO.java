package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.ComplaintStatus;
import com.yundao.bp.ops.entity.OpsComplaint;
import java.time.LocalDateTime;

/**
 * 投诉建议视图。
 */
public record ComplaintVO(
        Long id,
        String complaintNo,
        String complaintType,
        String source,
        String title,
        String content,
        String images,
        Long orgId,
        Long personId,
        String submitterName,
        String submitterPhone,
        String handleStatus,
        String handleStatusLabel,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        Integer satisfaction,
        Long workorderId,
        /** 派生：是否超时未处理（投诉类 48 小时未处理） */
        Boolean overdue,
        LocalDateTime createTime
) {
    public static ComplaintVO from(OpsComplaint e) {
        if (e == null) {
            return null;
        }
        ComplaintStatus st;
        try {
            st = ComplaintStatus.valueOf(e.getHandleStatus());
        } catch (IllegalArgumentException ex) {
            st = ComplaintStatus.PENDING;
        }
        boolean overdue = false;
        if (!st.isTerminal() && e.getCreateTime() != null
                && "COMPLAINT".equals(e.getComplaintType())) {
            overdue = LocalDateTime.now().isAfter(e.getCreateTime().plusHours(48));
        }
        return new ComplaintVO(e.getId(), e.getComplaintNo(), e.getComplaintType(), e.getSource(),
                e.getTitle(), e.getContent(), e.getImages(), e.getOrgId(), e.getPersonId(),
                e.getSubmitterName(), e.getSubmitterPhone(), e.getHandleStatus(), st.label(),
                e.getHandleUserId(), e.getHandleTime(), e.getHandleResult(), e.getSatisfaction(),
                e.getWorkorderId(), overdue, e.getCreateTime());
    }
}
