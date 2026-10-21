package com.yundao.bp.msg.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

/**
 * 发送消息。
 *
 * @param templateCode 模板编码（为空则直接使用 title/content 发送）
 * @param variables    模板变量（渲染 `${xxx}`）
 */
public record MessageSendCmd(

        String templateCode,

        @NotBlank(message = "业务类型不能为空")
        String bizType,

        Long bizId,

        /** 渠道；为空则按模板渠道 */
        String channel,

        String receiverType,
        String receiverId,
        String receiverName,
        String receiverAddr,

        /** 无模板时的直发标题/内容 */
        String title,
        String content,

        Map<String, Object> variables
) {
}
