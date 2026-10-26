package com.yundao.bp.rule.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.rule.engine.ThresholdEvaluator;
import com.yundao.bp.rule.entity.RuleExecuteLog;
import com.yundao.bp.rule.entity.RuleRule;
import com.yundao.bp.rule.entity.RuleRuleset;
import com.yundao.bp.rule.mapper.RuleExecuteLogMapper;
import com.yundao.bp.rule.mapper.RuleRuleMapper;
import com.yundao.bp.rule.mapper.RuleRulesetMapper;
import com.yundao.bp.rule.service.RuleEngineService;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 规则引擎实现。
 */
@Service
public class RuleEngineServiceImpl implements RuleEngineService {

    private static final Logger log = LoggerFactory.getLogger(RuleEngineServiceImpl.class);
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON =
            new com.fasterxml.jackson.databind.ObjectMapper();

    private final RuleRulesetMapper rulesetMapper;
    private final RuleRuleMapper ruleMapper;
    private final RuleExecuteLogMapper logMapper;
    private final ThresholdEvaluator evaluator;
    private final SnowflakeIdGenerator idGen;

    public RuleEngineServiceImpl(RuleRulesetMapper rulesetMapper, RuleRuleMapper ruleMapper,
                                 RuleExecuteLogMapper logMapper,
                                 ThresholdEvaluator evaluator, SnowflakeIdGenerator idGen) {
        this.rulesetMapper = rulesetMapper;
        this.ruleMapper = ruleMapper;
        this.logMapper = logMapper;
        this.evaluator = evaluator;
        this.idGen = idGen;
    }

    // ==================== 规则集 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRuleset createRuleset(String code, String name, String domain, String scenario,
                                     String securityType, Long orgId, String description) {
        if (code == null || code.isBlank()) {
            throw BizException.paramInvalid("规则集编码不能为空");
        }
        if (domain == null || domain.isBlank()) {
            throw BizException.paramInvalid("领域不能为空（ALERT/QUALIFY/BILLING）");
        }
        // 同编码递增版本号，历史版本保留可回溯
        List<RuleRuleset> olds = rulesetMapper.selectList(
                new LambdaQueryWrapper<RuleRuleset>()
                        .eq(RuleRuleset::getRulesetCode, code)
                        .orderByDesc(RuleRuleset::getRulesetVersion));
        int nextVer = olds.isEmpty() ? 1 : olds.get(0).getRulesetVersion() + 1;
        LocalDateTime now = LocalDateTime.now();
        RuleRuleset r = new RuleRuleset();
        r.setId(idGen.nextId());
        r.setTenantId(TenantContext.tenantId());
        r.setRulesetCode(code);
        r.setRulesetName(name == null ? code : name);
        r.setDomain(domain);
        r.setScenario(scenario);
        r.setSecurityType(securityType);
        r.setOrgId(orgId);
        r.setRulesetVersion(nextVer);
        r.setEffectiveStart(now);
        r.setRulesetStatus("DRAFT");
        r.setIsDefault(0);
        r.setDescription(description);
        r.setIsDeleted(0);
        r.setCreateTime(now);
        r.setUpdateTime(now);
        rulesetMapper.insert(r);
        log.info("规则集已创建：{} v{}（{}）", code, nextVer, domain);
        return r;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRuleset publish(Long rulesetId) {
        RuleRuleset r = requireRuleset(rulesetId);
        if ("PUBLISHED".equals(r.getRulesetStatus())) {
            throw BizException.stateConflict("该规则集已发布");
        }
        Long ruleCount = ruleMapper.selectCount(new LambdaQueryWrapper<RuleRule>()
                .eq(RuleRule::getRulesetId, rulesetId)
                .eq(RuleRule::getRuleStatus, "ENABLED"));
        if (ruleCount == null || ruleCount == 0) {
            throw BizException.stateConflict("规则集内没有启用的规则，不能发布");
        }
        // 同编码的其它已发布版本自动停用（保证同一时刻只有一个生效版本）
        List<RuleRuleset> others = rulesetMapper.selectList(
                new LambdaQueryWrapper<RuleRuleset>()
                        .eq(RuleRuleset::getRulesetCode, r.getRulesetCode())
                        .eq(RuleRuleset::getRulesetStatus, "PUBLISHED"));
        for (RuleRuleset o : others) {
            if (!o.getId().equals(rulesetId)) {
                o.setRulesetStatus("DISABLED");
                o.setEffectiveEnd(LocalDateTime.now());
                o.setUpdateTime(LocalDateTime.now());
                rulesetMapper.updateById(o);
                log.info("旧版本规则集已停用：{} v{}", o.getRulesetCode(),
                        o.getRulesetVersion());
            }
        }
        r.setRulesetStatus("PUBLISHED");
        r.setEffectiveStart(LocalDateTime.now());
        r.setUpdateTime(LocalDateTime.now());
        rulesetMapper.updateById(r);
        log.info("规则集已发布：{} v{}（{} 条启用规则）", r.getRulesetCode(),
                r.getRulesetVersion(), ruleCount);
        return r;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRuleset disable(Long rulesetId) {
        RuleRuleset r = requireRuleset(rulesetId);
        r.setRulesetStatus("DISABLED");
        r.setEffectiveEnd(LocalDateTime.now());
        r.setUpdateTime(LocalDateTime.now());
        rulesetMapper.updateById(r);
        return r;
    }

    @Override
    public List<RuleRuleset> listRulesets(String domain, String status) {
        return rulesetMapper.selectList(new LambdaQueryWrapper<RuleRuleset>()
                .eq(domain != null && !domain.isBlank(), RuleRuleset::getDomain, domain)
                .eq(status != null && !status.isBlank(),
                        RuleRuleset::getRulesetStatus, status)
                .orderByAsc(RuleRuleset::getRulesetCode)
                .orderByDesc(RuleRuleset::getRulesetVersion));
    }

    @Override
    public RuleRuleset resolveActive(String domain, String scenario, Long orgId) {
        List<RuleRuleset> list = rulesetMapper.selectList(
                new LambdaQueryWrapper<RuleRuleset>()
                        .eq(RuleRuleset::getDomain, domain)
                        .eq(scenario != null && !scenario.isBlank(),
                                RuleRuleset::getScenario, scenario)
                        .eq(RuleRuleset::getRulesetStatus, "PUBLISHED")
                        .orderByDesc(RuleRuleset::getIsDefault)
                        .orderByDesc(RuleRuleset::getRulesetVersion));
        LocalDateTime now = LocalDateTime.now();
        for (RuleRuleset r : list) {
            // 组织匹配：NULL 表示全租户适用
            if (r.getOrgId() != null && orgId != null && !r.getOrgId().equals(orgId)) {
                continue;
            }
            if (r.getEffectiveStart() != null && r.getEffectiveStart().isAfter(now)) {
                continue;
            }
            if (r.getEffectiveEnd() != null && r.getEffectiveEnd().isBefore(now)) {
                continue;
            }
            return r;
        }
        return null;
    }

    // ==================== 规则 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRule addRule(Long rulesetId, String code, String name, String conditionExpr,
                            String thresholdJson, String severity, String actionsJson,
                            Integer priority) {
        RuleRuleset rs = requireRuleset(rulesetId);
        if ("PUBLISHED".equals(rs.getRulesetStatus())) {
            throw BizException.stateConflict("已发布的规则集不可直接改规则，请新建版本");
        }
        if (code == null || code.isBlank()) {
            throw BizException.paramInvalid("规则编码不能为空");
        }
        // 阈值必须能被解析，避免运行时才发现配置错
        try {
            if (thresholdJson != null && !thresholdJson.isBlank()) {
                JSON.readTree(thresholdJson);
            }
        } catch (Exception e) {
            throw BizException.paramInvalid("阈值配置不是合法 JSON：" + e.getMessage());
        }
        Long dup = ruleMapper.selectCount(new LambdaQueryWrapper<RuleRule>()
                .eq(RuleRule::getRulesetId, rulesetId)
                .eq(RuleRule::getRuleCode, code));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED,
                    "该规则集内已存在规则编码：" + code);
        }
        LocalDateTime now = LocalDateTime.now();
        RuleRule r = new RuleRule();
        r.setId(idGen.nextId());
        r.setTenantId(TenantContext.tenantId());
        r.setRulesetId(rulesetId);
        r.setRuleCode(code);
        r.setRuleName(name == null ? code : name);
        r.setConditionExpr(conditionExpr);
        r.setThresholdJson(thresholdJson);
        r.setSeverity(severity == null ? "NORMAL" : severity);
        r.setActionsJson(actionsJson == null || actionsJson.isBlank() ? null : actionsJson);
        r.setPriority(priority == null ? 0 : priority);
        r.setRuleStatus("ENABLED");
        r.setIsDeleted(0);
        r.setCreateTime(now);
        r.setUpdateTime(now);
        ruleMapper.insert(r);
        return r;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRule updateRule(Long ruleId, String code, String name, String conditionExpr,
                               String thresholdJson, String severity, String actionsJson,
                               Integer priority) {
        RuleRule r = ruleMapper.selectById(ruleId);
        if (r == null) {
            throw BizException.notFound("规则");
        }
        RuleRuleset rs = requireRuleset(r.getRulesetId());
        if ("PUBLISHED".equals(rs.getRulesetStatus())) {
            throw BizException.stateConflict("已发布的规则集不可直接改规则，请新建版本");
        }
        if (code != null && !code.isBlank() && !code.equals(r.getRuleCode())) {
            Long dup = ruleMapper.selectCount(new LambdaQueryWrapper<RuleRule>()
                    .eq(RuleRule::getRulesetId, r.getRulesetId())
                    .eq(RuleRule::getRuleCode, code));
            if (dup != null && dup > 0) {
                throw new BizException(ErrorCode.DUPLICATED,
                        "该规则集内已存在规则编码：" + code);
            }
            r.setRuleCode(code);
        }
        try {
            if (thresholdJson != null && !thresholdJson.isBlank()) {
                JSON.readTree(thresholdJson);
            }
        } catch (Exception e) {
            throw BizException.paramInvalid("阈值配置不是合法 JSON：" + e.getMessage());
        }
        if (name != null && !name.isBlank()) {
            r.setRuleName(name);
        }
        r.setConditionExpr(conditionExpr);
        r.setThresholdJson(thresholdJson);
        if (severity != null && !severity.isBlank()) {
            r.setSeverity(severity);
        }
        r.setActionsJson(actionsJson == null || actionsJson.isBlank() ? null : actionsJson);
        if (priority != null) {
            r.setPriority(priority);
        }
        r.setUpdateTime(LocalDateTime.now());
        ruleMapper.updateById(r);
        return r;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RuleRule setRuleStatus(Long ruleId, String status) {
        RuleRule r = ruleMapper.selectById(ruleId);
        if (r == null) {
            throw BizException.notFound("规则");
        }
        if (!List.of("ENABLED", "DISABLED").contains(status)) {
            throw BizException.paramInvalid("非法规则状态：" + status);
        }
        r.setRuleStatus(status);
        r.setUpdateTime(LocalDateTime.now());
        ruleMapper.updateById(r);
        return r;
    }

    @Override
    public List<RuleRule> listRules(Long rulesetId) {
        return ruleMapper.selectList(new LambdaQueryWrapper<RuleRule>()
                .eq(RuleRule::getRulesetId, rulesetId)
                .orderByDesc(RuleRule::getPriority));
    }

    // ==================== 执行 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<Map<String, Object>> execute(Long rulesetId, String bizType, Long bizId,
                                             BigDecimal actual, Integer count,
                                             String eventType, BigDecimal total) {
        RuleRuleset rs = requireRuleset(rulesetId);
        if (!"PUBLISHED".equals(rs.getRulesetStatus())) {
            throw BizException.stateConflict(
                    "规则集未发布（" + rs.getRulesetStatus() + "），不能执行");
        }
        List<RuleRule> rules = ruleMapper.selectList(new LambdaQueryWrapper<RuleRule>()
                .eq(RuleRule::getRulesetId, rulesetId)
                .eq(RuleRule::getRuleStatus, "ENABLED")
                .orderByDesc(RuleRule::getPriority));
        List<Map<String, Object>> hits = new ArrayList<>();
        for (RuleRule rule : rules) {
            long t0 = System.currentTimeMillis();
            // 规则的阈值里可带 ruleType
            String ruleType = readRuleType(rule.getThresholdJson());
            ThresholdEvaluator.Result res = evaluator.evaluate(ruleType,
                    rule.getThresholdJson(), actual, count, eventType, total);
            int ms = (int) (System.currentTimeMillis() - t0);
            writeLog(rs, rule, bizType, bizId, res, actual, count, eventType, ms);
            if (res.hit()) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("ruleId", rule.getId());
                m.put("ruleCode", rule.getRuleCode());
                m.put("ruleName", rule.getRuleName());
                m.put("severity", rule.getSeverity());
                m.put("actions", rule.getActionsJson());
                m.put("actual", res.actual());
                m.put("explain", res.explain());
                hits.add(m);
            }
        }
        log.info("规则执行：规则集 {} 共 {} 条规则，命中 {} 条（biz={}）",
                rulesetId, rules.size(), hits.size(), bizType);
        return hits;
    }

    @Override
    public PageResult<RuleExecuteLog> pageLogs(long pageNum, long pageSize, Long rulesetId,
                                               Boolean hitOnly, String bizType) {
        LambdaQueryWrapper<RuleExecuteLog> qw = new LambdaQueryWrapper<RuleExecuteLog>()
                .eq(rulesetId != null, RuleExecuteLog::getRulesetId, rulesetId)
                .eq(Boolean.TRUE.equals(hitOnly), RuleExecuteLog::getHitFlag, 1)
                .eq(bizType != null && !bizType.isBlank(),
                        RuleExecuteLog::getBizType, bizType)
                .orderByDesc(RuleExecuteLog::getId);
        IPage<RuleExecuteLog> page = logMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    public Map<String, Object> hitStats(Long rulesetId) {
        LambdaQueryWrapper<RuleExecuteLog> qw = new LambdaQueryWrapper<RuleExecuteLog>();
        if (rulesetId != null) {
            qw.eq(RuleExecuteLog::getRulesetId, rulesetId);
        }
        List<RuleExecuteLog> all = logMapper.selectList(qw);
        Map<String, Integer> byRule = new LinkedHashMap<>();
        int hits = 0;
        for (RuleExecuteLog l : all) {
            if (l.getHitFlag() != null && l.getHitFlag() == 1) {
                hits++;
                byRule.merge(l.getRuleCode() == null ? "-" : l.getRuleCode(), 1,
                        Integer::sum);
            }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("executions", all.size());
        m.put("hits", hits);
        m.put("hitRate", all.isEmpty() ? 0.0
                : Math.round(hits * 10000.0 / all.size()) / 100.0);
        m.put("byRule", byRule);
        return m;
    }

    // ==================== 内部 ====================

    private RuleRuleset requireRuleset(Long id) {
        RuleRuleset r = rulesetMapper.selectById(id);
        if (r == null) {
            throw BizException.notFound("规则集");
        }
        return r;
    }

    /** 从阈值 JSON 读取 ruleType（缺省 THRESHOLD）。 */
    private static String readRuleType(String thresholdJson) {
        if (thresholdJson == null || thresholdJson.isBlank()) {
            return "THRESHOLD";
        }
        try {
            com.fasterxml.jackson.databind.JsonNode n = JSON.readTree(thresholdJson);
            return n.hasNonNull("ruleType") ? n.get("ruleType").asText() : "THRESHOLD";
        } catch (Exception e) {
            return "THRESHOLD";
        }
    }

    private void writeLog(RuleRuleset rs, RuleRule rule, String bizType, Long bizId,
                          ThresholdEvaluator.Result res, BigDecimal actual, Integer count,
                          String eventType, int ms) {
        try {
            RuleExecuteLog l = new RuleExecuteLog();
            l.setId(idGen.nextId());
            l.setTenantId(TenantContext.tenantId());
            l.setRulesetId(rs.getId());
            l.setRuleId(rule.getId());
            l.setRuleCode(rule.getRuleCode());
            l.setDomain(rs.getDomain());
            l.setBizType(bizType);
            l.setBizId(bizId);
            l.setHitFlag(res.hit() ? 1 : 0);
            Map<String, Object> in = new LinkedHashMap<>();
            in.put("actual", actual);
            in.put("count", count);
            in.put("eventType", eventType);
            l.setInputSnapshot(JSON.writeValueAsString(in));
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("hit", res.hit());
            out.put("explain", res.explain());
            l.setOutputSnapshot(JSON.writeValueAsString(out));
            l.setActionResult(res.hit()
                    ? ("命中，动作：" + (rule.getActionsJson() == null ? "无"
                            : rule.getActionsJson())) : "未命中");
            l.setDurationMs(ms);
            l.setExecuteTime(LocalDateTime.now());
            l.setCreateTime(LocalDateTime.now());
            logMapper.insert(l);
        } catch (Exception e) {
            log.warn("写规则执行日志失败（不影响主流程）：{}", e.getMessage());
        }
    }
}
