# -*- coding: utf-8 -*-
"""生成告警规则引擎：4 表实体 + Mapper + 求值器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(pkg, name, table, fields, doc, logic=False):
    li = 'import com.baomidou.mybatisplus.annotation.TableLogic;\n' if logic else ''
    lg = '\n    @TableLogic\n    private Integer isDeleted;\n' if logic else ''
    return f'''package com.yundao.bp.{pkg}.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{li}import java.time.LocalDateTime;
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
{lg}}}
'''


F['ops/entity/OpsAlertRule.java'] = ent('ops', 'OpsAlertRule', 'bp_ops_alert_rule', [
    '    private String tenantId;',
    '    private String ruleCode;',
    '    private String ruleName;',
    '    /** SAFETY / DEVICE / BUSINESS / VIOLATION */',
    '    private String ruleCategory;',
    '    /** EVENT_MATCH / TIME_WINDOW / RATIO / DURATION / THRESHOLD */',
    '    private String ruleType;',
    '    private String triggerEvent;',
    '    /** 条件表达式 */',
    '    private String conditionExpr;',
    '    /** 阈值配置 JSON（**自设阈值**的核心：不改代码即可调） */',
    '    private String thresholdJson;',
    '    /** URGENT / IMPORTANT / NORMAL */',
    '    private String severity;',
    '    /** 动作列表 JSON：NOTIFY / WORKORDER / FREEZE / TAG */',
    '    private String alertActions;',
    '    private String notifyChannels;',
    '    private String notifyReceivers;',
    '    private String scopeOrgIds;',
    '    /** 静默期（分钟内同一对象不重复告警） */',
    '    private Integer silenceMinutes;',
    '    private Integer escalateMinutes;',
    '    private String escalateTo;',
    '    private Integer priority;',
    '    /** ENABLED / DISABLED */',
    '    private String ruleStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], '告警规则。对应 `bp_ops_alert_rule`。', True)

F['rule/entity/RuleRuleset.java'] = ent('rule', 'RuleRuleset', 'bp_rule_ruleset', [
    '    private String tenantId;',
    '    private String rulesetCode;',
    '    private String rulesetName;',
    '    /** ALERT / QUALIFY / BILLING */',
    '    private String domain;',
    '    private String scenario;',
    '    private String securityType;',
    '    private Long orgId;',
    '    /** 版本号（同编码多版本共存，便于灰度与回溯） */',
    '    private Integer rulesetVersion;',
    '    private LocalDateTime effectiveStart;',
    '    private LocalDateTime effectiveEnd;',
    '    /** DRAFT / PUBLISHED / DISABLED */',
    '    private String rulesetStatus;',
    '    private Integer isDefault;',
    '    private String description;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], '规则集（按场景/地区版本化）。对应 `bp_rule_ruleset`。', True)

F['rule/entity/RuleRule.java'] = ent('rule', 'RuleRule', 'bp_rule_rule', [
    '    private String tenantId;',
    '    private Long rulesetId;',
    '    private String ruleCode;',
    '    private String ruleName;',
    '    private String conditionExpr;',
    '    /** 阈值参数 JSON（自设阈值） */',
    '    private String thresholdJson;',
    '    /** URGENT / IMPORTANT / NORMAL */',
    '    private String severity;',
    '    private String scoreExpr;',
    '    private String actionsJson;',
    '    /** 优先级（数值大者优先） */',
    '    private Integer priority;',
    '    /** ENABLED / DISABLED */',
    '    private String ruleStatus;',
    '    private String remark;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '规则集内的单条规则。对应 `bp_rule_rule`。', True)

F['rule/entity/RuleExecuteLog.java'] = ent('rule', 'RuleExecuteLog', 'bp_rule_execute_log', [
    '    private String tenantId;',
    '    private Long rulesetId;',
    '    private Long ruleId;',
    '    private String ruleCode;',
    '    /** ALERT / QUALIFY / BILLING */',
    '    private String domain;',
    '    private String bizType;',
    '    private Long bizId;',
    '    private Integer hitFlag;',
    '    private String inputSnapshot;',
    '    private String outputSnapshot;',
    '    private String actionResult;',
    '    private Integer durationMs;',
    '    private LocalDateTime executeTime;',
    '    private LocalDateTime createTime;',
], '规则执行日志（命中留痕，可回溯为什么告警/没告警）。对应 `bp_rule_execute_log`。')

for pkg, n in (('ops', 'OpsAlertRule'), ('rule', 'RuleRuleset'), ('rule', 'RuleRule'),
               ('rule', 'RuleExecuteLog')):
    F['%s/mapper/%sMapper.java' % (pkg, n)] = f'''package com.yundao.bp.{pkg}.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.{pkg}.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 阈值求值器（纯逻辑，可单测） ====================
F['rule/engine/ThresholdEvaluator.java'] = '''package com.yundao.bp.rule.engine;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import org.springframework.stereotype.Component;

/**
 * 阈值求值器（规则引擎的<b>纯函数内核</b>）。
 *
 * <p><b>为什么单独抽出来</b>：阈值判断是规则引擎最容易出错、也最需要
 * 「自设阈值」灵活性的部分。抽成纯函数后可以穷举测试，不必依赖数据库。
 *
 * <p>支持的规则类型：
 * <ul>
 *   <li>{@code THRESHOLD} 单阈值：value OP threshold，OP ∈ &gt; &gt;= &lt; &lt;= == !=</li>
 *   <li>{@code TIME_WINDOW} 时间窗统计：windowMinutes 内出现 countThreshold 次</li>
 *   <li>{@code RATIO} 比例阈值：ratio = part/total，超过 ratioThreshold 命中</li>
 *   <li>{@code DURATION} 持续时长：持续 minutes 分钟仍处于该状态</li>
 *   <li>{@code EVENT_MATCH} 事件匹配：eventType 属于 events 列表</li>
 * </ul>
 *
 * <p>阈值配置示例（存 `threshold_json`）：
 * <pre>
 * {"op": "&gt;", "value": 3}
 * {"windowMinutes": 30, "countThreshold": 5}
 * {"ratioThreshold": 0.2}
 * {"durationMinutes": 120}
 * {"events": ["access.duress", "device.offline"]}
 * </pre>
 */
@Component
public class ThresholdEvaluator {

    private static final ObjectMapper JSON = new ObjectMapper();

    /**
     * 求值结果。
     *
     * @param hit     是否命中
     * @param actual  实际值（用于告警正文与留痕）
     * @param explain 判定说明（为什么命中/未命中）
     */
    public record Result(boolean hit, BigDecimal actual, String explain) {
        public static Result of(boolean hit, BigDecimal actual, String explain) {
            return new Result(hit, actual, explain);
        }
    }

    /**
     * 按规则类型求值。
     *
     * @param ruleType      规则类型
     * @param thresholdJson 阈值配置
     * @param actual        实测值（THRESHOLD/RATIO/DURATION 用）
     * @param count         命中次数（TIME_WINDOW 用）
     * @param eventType     事件类型（EVENT_MATCH 用）
     * @param total         总量（RATIO 用，可空）
     */
    public Result evaluate(String ruleType, String thresholdJson, BigDecimal actual,
                           Integer count, String eventType, BigDecimal total) {
        String type = ruleType == null ? "THRESHOLD" : ruleType.trim().toUpperCase();
        JsonNode cfg;
        try {
            cfg = (thresholdJson == null || thresholdJson.isBlank())
                    ? JSON.createObjectNode() : JSON.readTree(thresholdJson);
        } catch (Exception e) {
            return Result.of(false, actual,
                    "阈值配置非法 JSON，规则被跳过：" + e.getMessage());
        }
        return switch (type) {
            case "THRESHOLD" -> threshold(cfg, actual);
            case "TIME_WINDOW" -> timeWindow(cfg, count, actual);
            case "RATIO" -> ratio(cfg, actual, total);
            case "DURATION" -> duration(cfg, actual);
            case "EVENT_MATCH" -> eventMatch(cfg, eventType);
            default -> Result.of(false, actual, "未知规则类型：" + type);
        };
    }

    // ---------- THRESHOLD ----------

    private Result threshold(JsonNode cfg, BigDecimal actual) {
        if (actual == null) {
            return Result.of(false, null, "未提供实测值，无法判定");
        }
        String op = cfg.hasNonNull("op") ? cfg.get("op").asText() : ">";
        BigDecimal th = cfg.hasNonNull("value")
                ? new BigDecimal(cfg.get("value").asText()) : BigDecimal.ZERO;
        int cmp = actual.compareTo(th);
        boolean hit = switch (op) {
            case ">" -> cmp > 0;
            case ">=" -> cmp >= 0;
            case "<" -> cmp < 0;
            case "<=" -> cmp <= 0;
            case "==", "=" -> cmp == 0;
            case "!=", "<>" -> cmp != 0;
            default -> false;
        };
        return Result.of(hit, actual, "实测 " + plain(actual) + " " + op + " 阈值 "
                + plain(th) + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- TIME_WINDOW ----------

    private Result timeWindow(JsonNode cfg, Integer count, BigDecimal actual) {
        int need = cfg.hasNonNull("countThreshold")
                ? cfg.get("countThreshold").asInt() : 1;
        int win = cfg.hasNonNull("windowMinutes")
                ? cfg.get("windowMinutes").asInt() : 0;
        int c = count == null ? (actual == null ? 0 : actual.intValue()) : count;
        boolean hit = c >= need;
        return Result.of(hit, BigDecimal.valueOf(c),
                win > 0 ? (win + " 分钟内发生 " + c + " 次，阈值 " + need + " 次"
                        + (hit ? " → 命中" : " → 未命中"))
                        : ("累计 " + c + " 次，阈值 " + need + " 次"
                                + (hit ? " → 命中" : " → 未命中")));
    }

    // ---------- RATIO ----------

    private Result ratio(JsonNode cfg, BigDecimal part, BigDecimal total) {
        BigDecimal t = total;
        if (t == null && cfg.hasNonNull("total")) {
            t = new BigDecimal(cfg.get("total").asText());
        }
        if (part == null || t == null || t.compareTo(BigDecimal.ZERO) == 0) {
            return Result.of(false, null, "比例计算缺少分母或分子，跳过（避免除零）");
        }
        BigDecimal r = part.divide(t, 4, RoundingMode.HALF_UP);
        BigDecimal th = cfg.hasNonNull("ratioThreshold")
                ? new BigDecimal(cfg.get("ratioThreshold").asText())
                : new BigDecimal("0.2");
        boolean hit = r.compareTo(th) >= 0;
        return Result.of(hit, r, "占比 " + r.multiply(BigDecimal.valueOf(100))
                .setScale(2, RoundingMode.HALF_UP) + "% "
                + (hit ? "≥" : "<") + " 阈值 "
                + th.multiply(BigDecimal.valueOf(100))
                .setScale(2, RoundingMode.HALF_UP) + "%"
                + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- DURATION ----------

    private Result duration(JsonNode cfg, BigDecimal minutes) {
        if (minutes == null) {
            return Result.of(false, null, "未提供持续时长，无法判定");
        }
        int need = cfg.hasNonNull("durationMinutes")
                ? cfg.get("durationMinutes").asInt() : 60;
        boolean hit = minutes.compareTo(BigDecimal.valueOf(need)) >= 0;
        return Result.of(hit, minutes, "已持续 " + plain(minutes) + " 分钟，阈值 "
                + need + " 分钟" + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- EVENT_MATCH ----------

    private Result eventMatch(JsonNode cfg, String eventType) {
        if (eventType == null) {
            return Result.of(false, null, "未提供事件类型，无法判定");
        }
        if (!cfg.has("events") || !cfg.get("events").isArray()) {
            return Result.of(false, null, "阈值配置缺少 events 数组，规则被跳过");
        }
        boolean found = false;
        for (JsonNode n : cfg.get("events")) {
            String e = n.asText();
            if (e.equals(eventType)) {
                found = true;
                break;
            }
            // 支持前缀通配：access.*
            if (e.endsWith("*") && eventType.startsWith(e.substring(0, e.length() - 1))) {
                found = true;
                break;
            }
        }
        return Result.of(found, null, "事件 " + eventType
                + (found ? " 在告警事件清单内 → 命中" : " 不在清单内 → 未命中"));
    }

    private static String plain(BigDecimal v) {
        return v == null ? "-" : v.stripTrailingZeros().toPlainString();
    }

    /** 便捷方法：单阈值判定。 */
    public boolean over(BigDecimal actual, String op, BigDecimal threshold) {
        String cfg = "{\\"op\\":\\"" + op + "\\",\\"value\\":" + threshold.toPlainString() + "}";
        return evaluate("THRESHOLD", cfg, actual, null, null, null).hit();
    }

    /** 列出支持的规则类型（供前端下拉与字典对齐）。 */
    public List<String> supportedTypes() {
        return List.of("THRESHOLD", "TIME_WINDOW", "RATIO", "DURATION", "EVENT_MATCH");
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
