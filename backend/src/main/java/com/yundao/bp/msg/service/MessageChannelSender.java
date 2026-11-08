package com.yundao.bp.msg.service;

/** 短信/微信通道发送适配器。 */
public interface MessageChannelSender {

    SendResult send(String channel, String receiverAddr, String title, String content);

    record SendResult(boolean success, String thirdMsgId, String error) {
        public static SendResult simulated(String channel, long messageId) {
            return new SendResult(true, "SIM-" + channel + "-" + messageId, null);
        }
    }
}
