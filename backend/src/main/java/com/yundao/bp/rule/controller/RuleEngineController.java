package com.yundao.bp.rule.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.rule.entity.RuleExecuteLog;
import com.yundao.bp.rule.entity.RuleRule;
import com.yundao.bp.rule.entity.RuleRuleset;
import com.yundao.bp.rule.service.RuleEngineService;
import com.yundao.bp.sys.audit.Audit;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 规则引擎接口（自设阈值 + 版本化规则集）。
 */
@RestController
@RequestMapping("/api/v1/rules")
public class RuleEngineController {

    private final RuleEngineService service;

    public RuleEngineController(RuleEngineService service) {
        this.service = service;
    }

    // ---------- 规则集 ----------

    /** ⭐ 新建规则集（同编码自动递增版本）。 */
    @PostMapping("/rulesets")
    @RequirePerm("rule:ruleset:manage")
    @Audit(type = "CONFIG", level = "IMPORTANT", action = "新建规则集")
    public R<RuleRuleset> create(@RequestBody RulesetCmd cmd) {
        return R.ok(service.createRuleset(cmd.code(), cmd.name(), cmd.domain(),
                cmd.scenario(), cmd.securityType(), cmd.orgId(), cmd.description()));
    }

    /** ⭐ 发布规则集（同编码旧版本自动停用）。 */
    @PostMapping("/rulesets/{id}/publish")
    @RequirePerm("rule:ruleset:manage")
    @Audit(type = "CONFIG", level = "CRITICAL", action = "发布规则集")
    public R<RuleRuleset> publish(@PathVariable Long id) {
        return R.ok(service.publish(id));
    }

    @PostMapping("/rulesets/{id}/disable")
    @RequirePerm("rule:ruleset:manage")
    @Audit(type = "CONFIG", level = "IMPORTANT", action = "停用规则集")
    public R<RuleRuleset> disable(@PathVariable Long id) {
        return R.ok(service.disable(id));
    }

    @GetMapping("/rulesets")
    public R<List<RuleRuleset>> rulesets(@RequestParam(required = false) String domain,
                                         @RequestParam(required = false) String status) {
        return R.ok(service.listRulesets(domain, status));
    }

    /** ⭐ 取当前生效规则集（按场景/组织解析）。 */
    @com.yundao.bp.iam.security.RequirePerm("rules:rulesets:view")
    @GetMapping("/rulesets/active")
    public R<RuleRuleset> active(@RequestParam String domain,
                                 @RequestParam(required = false) String scenario,
                                 @RequestParam(required = false) Long orgId) {
        return R.ok(service.resolveActive(domain, scenario, orgId));
    }

    // ---------- 规则 ----------

    /** ⭐ 新增规则（阈值必须是合法 JSON；已发布规则集不可改）。 */
    @PostMapping("/rulesets/{id}/rules")
    @RequirePerm("rule:ruleset:manage")
    @Audit(type = "CONFIG", level = "IMPORTANT", action = "新增规则")
    public R<RuleRule> addRule(@PathVariable Long id, @RequestBody RuleCmd cmd) {
        return R.ok(service.addRule(id, cmd.code(), cmd.name(), cmd.conditionExpr(),
                cmd.thresholdJson(), cmd.severity(), cmd.actionsJson(), cmd.priority()));
    }

    @PostMapping("/rules/{id}/status")
    @RequirePerm("rule:ruleset:manage")
    public R<RuleRule> ruleStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(service.setRuleStatus(id, cmd.status()));
    }

    @GetMapping("/rulesets/{id}/rules")
    public R<List<RuleRule>> rules(@PathVariable Long id) {
        return R.ok(service.listRules(id));
    }

    // ---------- 执行 ----------

    /** ⭐ 执行规则集（返回命中规则与判定说明）。 */
    @com.yundao.bp.iam.security.RequirePerm("rules:rulesets:execute")
    @PostMapping("/rulesets/{id}/execute")
    public R<List<Map<String, Object>>> execute(@PathVariable Long id,
                                                @RequestBody ExecuteCmd cmd) {
        return R.ok(service.execute(id, cmd.bizType(), cmd.bizId(), cmd.actual(),
                cmd.count(), cmd.eventType(), cmd.total()));
    }

    @GetMapping("/logs")
    @RequirePerm("rule:log:list")
    public R<PageResult<RuleExecuteLog>> logs(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long rulesetId,
            @RequestParam(required = false) Boolean hitOnly,
            @RequestParam(required = false) String bizType) {
        return R.ok(service.pageLogs(pageNum, pageSize, rulesetId, hitOnly, bizType));
    }

    /** ⭐ 命中统计（哪条规则最常触发）。 */
    @com.yundao.bp.iam.security.RequirePerm("rules:stats:view")
    @GetMapping("/stats")
    public R<Map<String, Object>> stats(@RequestParam(required = false) Long rulesetId) {
        return R.ok(service.hitStats(rulesetId));
    }

    private static String operator() {
        LoginUser u = LoginUser.get();
        return u == null ? "system" : (u.realName() == null ? u.username() : u.realName());
    }

    public record RulesetCmd(String code, String name, String domain, String scenario,
                             String securityType, Long orgId, String description) {
    }

    public record RuleCmd(String code, String name, String conditionExpr,
                          String thresholdJson, String severity, String actionsJson,
                          Integer priority) {
    }

    public record StatusCmd(String status) {
    }

    public record ExecuteCmd(String bizType, Long bizId, BigDecimal actual, Integer count,
                             String eventType, BigDecimal total) {
    }
}
