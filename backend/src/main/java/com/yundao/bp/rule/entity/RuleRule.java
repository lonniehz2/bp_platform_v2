package com.yundao.bp.rule.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 规则集内的单条规则。对应 `bp_rule_rule`。
 */
@Data
@TableName("bp_rule_rule")
public class RuleRule {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long rulesetId;
    private String ruleCode;
    private String ruleName;
    private String conditionExpr;
    /** 阈值参数 JSON（自设阈值） */
    private String thresholdJson;
    /** URGENT / IMPORTANT / NORMAL */
    private String severity;
    private String scoreExpr;
    private String actionsJson;
    /** 优先级（数值大者优先） */
    private Integer priority;
    /** ENABLED / DISABLED */
    private String ruleStatus;
    private String remark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
