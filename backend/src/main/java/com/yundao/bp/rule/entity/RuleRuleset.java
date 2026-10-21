package com.yundao.bp.rule.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 规则集（按场景/地区版本化）。对应 `bp_rule_ruleset`。
 */
@Data
@TableName("bp_rule_ruleset")
public class RuleRuleset {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String rulesetCode;
    private String rulesetName;
    /** ALERT / QUALIFY / BILLING */
    private String domain;
    private String scenario;
    private String securityType;
    private Long orgId;
    /** 版本号（同编码多版本共存，便于灰度与回溯） */
    private Integer rulesetVersion;
    private LocalDateTime effectiveStart;
    private LocalDateTime effectiveEnd;
    /** DRAFT / PUBLISHED / DISABLED */
    private String rulesetStatus;
    private Integer isDefault;
    private String description;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
