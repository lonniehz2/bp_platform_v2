package com.yundao.bp.rule.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.rule.entity.RuleExecuteLog;
import com.yundao.bp.rule.entity.RuleRule;
import com.yundao.bp.rule.entity.RuleRuleset;
import java.util.List;
import java.util.Map;

/**
 * 规则引擎服务。
 *
 * <p><b>设计要点</b>：
 * <ul>
 *   <li><b>规则集版本化</b>：同编码可多版本共存（DRAFT/PUBLISHED），
 *       支持灰度与回溯（「上月用的是哪版阈值」可查）</li>
 *   <li><b>阈值外置</b>：阈值存 {@code threshold_json}，改阈值不改代码——
 *       直接满足「自设阈值」要求</li>
 *   <li><b>命中留痕</b>：每次执行写 {@code bp_rule_execute_log}，
 *       能回答「为什么这次没告警」</li>
 * </ul>
 */
public interface RuleEngineService {

    // ---------- 规则集 ----------

    RuleRuleset createRuleset(String code, String name, String domain, String scenario,
                              String securityType, Long orgId, String description);

    /** 发布（DRAFT → PUBLISHED；同编码旧版本自动转 DISABLED）。 */
    RuleRuleset publish(Long rulesetId);

    /** 停用。 */
    RuleRuleset disable(Long rulesetId);

    List<RuleRuleset> listRulesets(String domain, String status);

    /** 取某场景下生效的规则集（默认优先、已发布、在有效期）。 */
    RuleRuleset resolveActive(String domain, String scenario, Long orgId);

    // ---------- 规则 ----------

    /** 修改规则（仅未发布的规则集可改）。 */
    RuleRule updateRule(Long ruleId, String code, String name, String conditionExpr,
                        String thresholdJson, String severity, String actionsJson,
                        Integer priority);

    RuleRule addRule(Long rulesetId, String code, String name, String conditionExpr,
                     String thresholdJson, String severity, String actionsJson,
                     Integer priority);

    RuleRule setRuleStatus(Long ruleId, String status);

    List<RuleRule> listRules(Long rulesetId);

    // ---------- 执行 ----------

    /**
     * 按规则集执行一组实测输入，返回命中规则。
     *
     * @param rulesetId 规则集
     * @param bizType   业务类型
     * @param bizId     业务单据
     * @param actual    实测值
     * @param count     次数（时间窗规则用）
     * @param eventType 事件类型
     * @param total     总量（比例规则用）
     * @return 命中结果列表（含告警级别与动作）
     */
    List<Map<String, Object>> execute(Long rulesetId, String bizType, Long bizId,
                                      java.math.BigDecimal actual, Integer count,
                                      String eventType, java.math.BigDecimal total);

    PageResult<RuleExecuteLog> pageLogs(long pageNum, long pageSize, Long rulesetId,
                                        Boolean hitOnly, String bizType);

    /** 规则命中统计（看板：哪条规则最常触发）。 */
    Map<String, Object> hitStats(Long rulesetId);
}
