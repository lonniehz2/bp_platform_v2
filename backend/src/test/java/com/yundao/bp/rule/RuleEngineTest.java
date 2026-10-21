package com.yundao.bp.rule;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.rule.engine.ThresholdEvaluator;
import com.yundao.bp.rule.entity.RuleExecuteLog;
import com.yundao.bp.rule.entity.RuleRule;
import com.yundao.bp.rule.entity.RuleRuleset;
import com.yundao.bp.rule.mapper.RuleExecuteLogMapper;
import com.yundao.bp.rule.mapper.RuleRuleMapper;
import com.yundao.bp.rule.mapper.RuleRulesetMapper;
import com.yundao.bp.rule.service.impl.RuleEngineServiceImpl;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 规则集版本控制与执行测试。
 *
 * <p>重点：<b>同一时刻只有一个版本生效</b>、<b>已发布不可改规则</b>、
 * <b>发布前必须有启用规则</b>。这些约束保证「上月用的哪版阈值」可回溯。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class RuleEngineTest {

    @Mock
    private RuleRulesetMapper rulesetMapper;
    @Mock
    private RuleRuleMapper ruleMapper;
    @Mock
    private RuleExecuteLogMapper logMapper;

    private RuleEngineServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new RuleEngineServiceImpl(rulesetMapper, ruleMapper, logMapper,
                new ThresholdEvaluator(), new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(rulesetMapper.insert(any(RuleRuleset.class))).thenReturn(1);
        when(rulesetMapper.updateById(any(RuleRuleset.class))).thenReturn(1);
        when(ruleMapper.insert(any(RuleRule.class))).thenReturn(1);
        // MyBatis-Plus 3.5.7 的 insert 有单条与批量两个重载，必须显式指定类型
        when(logMapper.insert(any(RuleExecuteLog.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static RuleRuleset ruleset(long id, String code, int ver, String status) {
        RuleRuleset r = new RuleRuleset();
        r.setId(id);
        r.setTenantId("350600");
        r.setRulesetCode(code);
        r.setRulesetName(code);
        r.setDomain("ALERT");
        r.setRulesetVersion(ver);
        r.setRulesetStatus(status);
        r.setIsDefault(0);
        r.setIsDeleted(0);
        return r;
    }

    private static RuleRule rule(long id, long rsId, String code, String threshold,
                                 String status) {
        RuleRule r = new RuleRule();
        r.setId(id);
        r.setRulesetId(rsId);
        r.setRuleCode(code);
        r.setRuleName(code);
        r.setThresholdJson(threshold);
        r.setSeverity("URGENT");
        r.setPriority(10);
        r.setRuleStatus(status);
        return r;
    }

    // ==================== 版本控制 ====================

    @Test
    @DisplayName("⭐ 同编码新建规则集 → 版本号自动递增")
    void versionIncrement() {
        when(rulesetMapper.selectList(any()))
                .thenReturn(List.of(ruleset(1, "ALERT-01", 3, "PUBLISHED")));
        RuleRuleset r = service.createRuleset("ALERT-01", "欠费预警", "ALERT", null,
                null, null, null);
        assertEquals(4, r.getRulesetVersion(), "应递增到 v4");
        assertEquals("DRAFT", r.getRulesetStatus(), "新版本应为草稿");
    }

    @Test
    @DisplayName("首个版本号为 1")
    void firstVersion() {
        when(rulesetMapper.selectList(any())).thenReturn(List.of());
        assertEquals(1, service.createRuleset("NEW", "新规则集", "ALERT", null, null,
                null, null).getRulesetVersion());
    }

    @Test
    @DisplayName("⭐ 缺规则集编码/领域 → 拒绝")
    void createValidation() {
        assertThrows(BizException.class,
                () -> service.createRuleset(null, "x", "ALERT", null, null, null, null));
        assertThrows(BizException.class,
                () -> service.createRuleset("C", "x", null, null, null, null, null));
    }

    // ==================== 发布约束 ====================

    @Test
    @DisplayName("⭐⭐ 无启用规则不能发布（防空规则集上线）")
    void publishRequiresRules() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "ALERT-01", 1, "DRAFT"));
        when(ruleMapper.selectCount(any())).thenReturn(0L);
        BizException ex = assertThrows(BizException.class, () -> service.publish(1L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("没有启用的规则"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐⭐ 发布新版本 → 同编码旧版本自动停用（只留一个生效）")
    void publishDisablesOldVersion() {
        RuleRuleset cur = ruleset(2, "ALERT-01", 2, "DRAFT");
        RuleRuleset old = ruleset(1, "ALERT-01", 1, "PUBLISHED");
        when(rulesetMapper.selectById(2L)).thenReturn(cur);
        when(ruleMapper.selectCount(any())).thenReturn(3L);
        when(rulesetMapper.selectList(any())).thenReturn(List.of(old));

        RuleRuleset out = service.publish(2L);
        assertEquals("PUBLISHED", out.getRulesetStatus());
        assertEquals("DISABLED", old.getRulesetStatus(), "旧版本必须停用");
        assertTrue(old.getEffectiveEnd() != null, "旧版本应记录失效时间");
    }

    @Test
    @DisplayName("重复发布 → 拒绝")
    void publishTwice() {
        when(rulesetMapper.selectById(1L))
                .thenReturn(ruleset(1, "A", 1, "PUBLISHED"));
        assertThrows(BizException.class, () -> service.publish(1L));
    }

    // ==================== 规则维护 ====================

    @Test
    @DisplayName("⭐⭐ 已发布的规则集不可直接改规则（须新建版本）")
    void cannotAddRuleToPublished() {
        when(rulesetMapper.selectById(1L))
                .thenReturn(ruleset(1, "A", 1, "PUBLISHED"));
        BizException ex = assertThrows(BizException.class,
                () -> service.addRule(1L, "R1", "规则1", null, "{}", "URGENT", null, 1));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("新建版本"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 阈值非法 JSON 在录入时就拒绝（不等到运行时报错）")
    void invalidThresholdRejectedAtEntry() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "DRAFT"));
        BizException ex = assertThrows(BizException.class,
                () -> service.addRule(1L, "R1", "规则1", null, "not-json", "URGENT",
                        null, 1));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("合法 JSON"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 同规则集内规则编码不可重复")
    void duplicateRuleCode() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "DRAFT"));
        when(ruleMapper.selectCount(any())).thenReturn(1L);
        BizException ex = assertThrows(BizException.class,
                () -> service.addRule(1L, "R1", "规则1", null, "{}", "URGENT", null, 1));
        assertEquals(ErrorCode.DUPLICATED, ex.errorCode());
    }

    // ==================== 执行 ====================

    @Test
    @DisplayName("⭐⭐ 未发布规则集不能执行")
    void executeRequiresPublished() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "DRAFT"));
        BizException ex = assertThrows(BizException.class,
                () -> service.execute(1L, "ARREARS", 1L, BigDecimal.TEN, null, null, null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐⭐ 执行只返回命中规则，并按优先级倒序")
    void executeReturnsHits() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "PUBLISHED"));
        RuleRule hit = rule(1, 1, "AMOUNT_HIGH",
                "{\"ruleType\":\"THRESHOLD\",\"op\":\">\",\"value\":3000}", "ENABLED");
        RuleRule miss = rule(2, 1, "AMOUNT_LOW",
                "{\"ruleType\":\"THRESHOLD\",\"op\":\">\",\"value\":99999}", "ENABLED");
        when(ruleMapper.selectList(any())).thenReturn(List.of(hit, miss));

        List<Map<String, Object>> hits = service.execute(1L, "ARREARS", 9L,
                new BigDecimal("5000"), null, null, null);
        assertEquals(1, hits.size(), String.valueOf(hits));
        assertEquals("AMOUNT_HIGH", hits.get(0).get("ruleCode"));
        assertEquals("URGENT", hits.get(0).get("severity"));
        assertTrue(String.valueOf(hits.get(0).get("explain")).contains("命中"));
    }

    @Test
    @DisplayName("⭐ 无命中返回空列表（不是 null）")
    void executeNoHits() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "PUBLISHED"));
        when(ruleMapper.selectList(any())).thenReturn(List.of(
                rule(1, 1, "R", "{\"op\":\">\",\"value\":99999}", "ENABLED")));
        assertTrue(service.execute(1L, "X", 1L, BigDecimal.ONE, null, null, null).isEmpty());
    }

    @Test
    @DisplayName("⭐⭐ 每次执行都写日志（命中与未命中都留痕，可回答「为何没告警」）")
    void executeWritesLogForAllRules() {
        when(rulesetMapper.selectById(1L)).thenReturn(ruleset(1, "A", 1, "PUBLISHED"));
        when(ruleMapper.selectList(any())).thenReturn(List.of(
                rule(1, 1, "HIT", "{\"op\":\">\",\"value\":1}", "ENABLED"),
                rule(2, 1, "MISS", "{\"op\":\">\",\"value\":9999}", "ENABLED")));

        service.execute(1L, "X", 1L, BigDecimal.TEN, null, null, null);
        org.mockito.Mockito.verify(logMapper, org.mockito.Mockito.times(2))
                .insert(any(RuleExecuteLog.class));
    }

    // ==================== 统计 ====================

    @Test
    @DisplayName("⭐ 命中统计：命中率与按规则分布")
    void hitStats() {
        RuleExecuteLogStub a = new RuleExecuteLogStub(1, "R1");
        RuleExecuteLogStub b = new RuleExecuteLogStub(0, "R1");
        RuleExecuteLogStub c = new RuleExecuteLogStub(1, "R2");
        when(logMapper.selectList(any())).thenReturn(List.of(a.log(), b.log(), c.log()));

        Map<String, Object> s = service.hitStats(1L);
        assertEquals(3, s.get("executions"));
        assertEquals(2, s.get("hits"));
        Map<?, ?> byRule = (Map<?, ?>) s.get("byRule");
        assertEquals(1, byRule.get("R1"));
        assertEquals(1, byRule.get("R2"));
    }

    /** 简化构造 execute log。 */
    private record RuleExecuteLogStub(int hit, String code) {
        com.yundao.bp.rule.entity.RuleExecuteLog log() {
            com.yundao.bp.rule.entity.RuleExecuteLog l =
                    new com.yundao.bp.rule.entity.RuleExecuteLog();
            l.setHitFlag(hit);
            l.setRuleCode(code);
            return l;
        }
    }
}
