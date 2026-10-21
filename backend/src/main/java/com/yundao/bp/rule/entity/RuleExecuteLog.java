package com.yundao.bp.rule.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 规则执行日志（命中留痕，可回溯为什么告警/没告警）。对应 `bp_rule_execute_log`。
 */
@Data
@TableName("bp_rule_execute_log")
public class RuleExecuteLog {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long rulesetId;
    private Long ruleId;
    private String ruleCode;
    /** ALERT / QUALIFY / BILLING */
    private String domain;
    private String bizType;
    private Long bizId;
    private Integer hitFlag;
    private String inputSnapshot;
    private String outputSnapshot;
    private String actionResult;
    private Integer durationMs;
    private LocalDateTime executeTime;
    private LocalDateTime createTime;
}
