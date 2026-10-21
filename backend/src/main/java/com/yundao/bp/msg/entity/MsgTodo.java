package com.yundao.bp.msg.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 站内待办。对应 `bp_msg_todo`。
 */
@Data
@TableName("bp_msg_todo")
public class MsgTodo {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long userId;
    /** APPROVE / HANDLE / ALERT / REMIND */
    private String todoType;
    private String title;
    private String content;
    private String bizType;
    private Long bizId;
    private String linkUrl;
    /** URGENT / IMPORTANT / NORMAL */
    private String priority;
    /** PENDING / READ / DONE */
    private String todoStatus;
    private LocalDateTime expireTime;
    private LocalDateTime createTime;
    private LocalDateTime readTime;
    private LocalDateTime doneTime;
}
