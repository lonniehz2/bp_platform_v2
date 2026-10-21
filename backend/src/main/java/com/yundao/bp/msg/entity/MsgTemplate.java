package com.yundao.bp.msg.entity;

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
