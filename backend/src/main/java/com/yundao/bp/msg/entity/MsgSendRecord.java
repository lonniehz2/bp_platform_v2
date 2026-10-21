package com.yundao.bp.msg.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 消息发送记录。对应 `bp_msg_send_record`。
 */
@Data
@TableName("bp_msg_send_record")
public class MsgSendRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String messageNo;
    private String templateCode;
    private String channel;
    private String bizType;
    private Long bizId;

    private String receiverType;
    private String receiverId;
    private String receiverName;
    private String receiverAddr;

    private String title;
    private String content;

    /** PENDING / SENDING / SUCCESS / FAILED */
    private String sendStatus;
    private Integer retryCount;
    private String failReason;
    private String thirdMsgId;

    private LocalDateTime planTime;
    private LocalDateTime sendTime;
    private LocalDateTime deliverTime;
    private LocalDateTime createTime;
}
