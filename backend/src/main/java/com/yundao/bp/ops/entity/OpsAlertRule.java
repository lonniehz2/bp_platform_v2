package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 告警规则。对应 `bp_ops_alert_rule`。
 */
@Data
@TableName("bp_ops_alert_rule")
public class OpsAlertRule {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String ruleCode;
    private String ruleName;
    /** SAFETY / DEVICE / BUSINESS / VIOLATION */
    private String ruleCategory;
    /** EVENT_MATCH / TIME_WINDOW / RATIO / DURATION / THRESHOLD */
    private String ruleType;
    private String triggerEvent;
    /** 条件表达式 */
    private String conditionExpr;
    /** 阈值配置 JSON（**自设阈值**的核心：不改代码即可调） */
    private String thresholdJson;
    /** URGENT / IMPORTANT / NORMAL */
    private String severity;
    /** 动作列表 JSON：NOTIFY / WORKORDER / FREEZE / TAG */
    private String alertActions;
    private String notifyChannels;
    private String notifyReceivers;
    private String scopeOrgIds;
    /** 静默期（分钟内同一对象不重复告警） */
    private Integer silenceMinutes;
    private Integer escalateMinutes;
    private String escalateTo;
    private Integer priority;
    /** ENABLED / DISABLED */
    private String ruleStatus;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
