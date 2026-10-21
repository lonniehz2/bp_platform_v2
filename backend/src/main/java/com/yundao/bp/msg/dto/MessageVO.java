package com.yundao.bp.msg.dto;

import com.yundao.bp.msg.entity.MsgSendRecord;
import java.time.LocalDateTime;

/**
 * 消息视图。
 */
public record MessageVO(
        Long id,
        String messageNo,
        String templateCode,
        String channel,
        String bizType,
        Long bizId,
        String receiverId,
        String receiverName,
        String receiverAddr,
        String title,
        String content,
        String sendStatus,
        Integer retryCount,
        String failReason,
        LocalDateTime sendTime,
        LocalDateTime createTime
) {
    public static MessageVO from(MsgSendRecord e) {
        if (e == null) {
            return null;
        }
        return new MessageVO(e.getId(), e.getMessageNo(), e.getTemplateCode(), e.getChannel(),
                e.getBizType(), e.getBizId(), e.getReceiverId(), e.getReceiverName(),
                e.getReceiverAddr(), e.getTitle(), e.getContent(), e.getSendStatus(),
                e.getRetryCount(), e.getFailReason(), e.getSendTime(), e.getCreateTime());
    }
}
