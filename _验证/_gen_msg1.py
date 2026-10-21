# -*- coding: utf-8 -*-
"""生成消息中心：实体 + Mapper + 服务 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 实体 ====================
F['msg/entity/MsgTemplate.java'] = '''package com.yundao.bp.msg.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 消息模板。对应 `bp_msg_template`。
 *
 * <p>内容支持 `${变量}` 占位符；租户可覆盖系统内置模板
 * （{@code tenant_id} 为空表示系统内置）。
 */
@Data
@TableName("bp_msg_template")
public class MsgTemplate {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String templateCode;
    private String templateName;
    /** SMS / WECHAT / APP_PUSH / INNER / EMAIL / PLATFORM */
    private String channel;
    private String bizType;
    private String titleTpl;
    private String contentTpl;
    private String variables;
    private String thirdTplId;
    /** ENABLED / DISABLED */
    private String templateStatus;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

F['msg/entity/MsgSubscription.java'] = '''package com.yundao.bp.msg.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 消息订阅配置。对应 `bp_msg_subscription`。
 */
@Data
@TableName("bp_msg_subscription")
public class MsgSubscription {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String bizType;
    /** ROLE / USER / PERSON / EXTERNAL */
    private String subscriberType;
    private String subscriberId;
    /** 渠道（逗号分隔） */
    private String channels;
    private String filterExpr;
    /** ENABLED / DISABLED */
    private String subStatus;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

F['msg/entity/MsgSendRecord.java'] = '''package com.yundao.bp.msg.entity;

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
'''

F['msg/entity/MsgTodo.java'] = '''package com.yundao.bp.msg.entity;

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
'''

for n in ('MsgTemplate', 'MsgSubscription', 'MsgSendRecord', 'MsgTodo'):
    F['msg/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.msg.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.msg.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== DTO ====================
F['msg/dto/MessageSendCmd.java'] = '''package com.yundao.bp.msg.dto;

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
'''

F['msg/dto/MessageVO.java'] = '''package com.yundao.bp.msg.dto;

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
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
