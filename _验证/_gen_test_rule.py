# -*- coding: utf-8 -*-
"""生成规则引擎测试：阈值求值 + 规则集版本控制"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\rule'

EVAL = r'''package com.yundao.bp.rule;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.rule.engine.ThresholdEvaluator;
import java.math.BigDecimal;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 阈值求值测试（规则引擎内核）。
 *
 * <p><b>为什么必须测</b>：这是「自设阈值」的执行核心。
 * 阈值配错会直接导致该告警的不告警（漏报）或天天误报（疲劳）。
 * 求值是纯函数，可以穷举边界。
 */
class ThresholdEvaluatorTest {

    private final ThresholdEvaluator ev = new ThresholdEvaluator();

    private static BigDecimal n(String s) {
        return new BigDecimal(s);
    }

    // ==================== THRESHOLD ====================

    @Test
    @DisplayName("⭐ 大于阈值命中（拖欠金额 > 3000）")
    void greaterThan() {
        var r = ev.evaluate("THRESHOLD", "{\"op\":\">\",\"value\":3000}",
                n("3200"), null, null, null);
        assertTrue(r.hit(), r.explain());
        assertTrue(r.explain().contains("命中"), r.explain());
    }

    @Test
    @DisplayName("⭐ 恰好等于阈值：> 不命中，>= 命中（边界必须分开）")
    void equalBoundary() {
        assertFalse(ev.evaluate("THRESHOLD", "{\"op\":\">\",\"value\":3000}",
                n("3000"), null, null, null).hit());
        assertTrue(ev.evaluate("THRESHOLD", "{\"op\":\">=\",\"value\":3000}",
                n("3000"), null, null, null).hit());
    }

    @Test
    @DisplayName("全部比较运算符")
    void allOps() {
        String v = "100";
        assertTrue(ev.over(n("101"), ">", n(v)));
        assertFalse(ev.over(n("100"), ">", n(v)));
        assertTrue(ev.over(n("100"), ">=", n(v)));
        assertTrue(ev.over(n("99"), "<", n(v)));
        assertTrue(ev.over(n("100"), "<=", n(v)));
        assertTrue(ev.over(n("100"), "==", n(v)));
        assertTrue(ev.over(n("101"), "!=", n(v)));
        assertFalse(ev.over(n("101"), "==", n(v)));
    }

    @Test
    @DisplayName("缺实测值 → 不命中且说明原因（不能默认为 0 触发误报）")
    void nullActual() {
        var r = ev.evaluate("THRESHOLD", "{\"op\":\">\",\"value\":10}",
                null, null, null, null);
        assertFalse(r.hit());
        assertEquals(null, r.actual());
        assertTrue(r.explain().contains("未提供实测值"), r.explain());
    }

    @Test
    @DisplayName("阈值缺 value → 默认按 0 比较")
    void defaultValue() {
        assertTrue(ev.evaluate("THRESHOLD", "{\"op\":\">\"}", n("1"),
                null, null, null).hit());
    }

    // ==================== TIME_WINDOW ====================

    @Test
    @DisplayName("⭐ 时间窗：30 分钟内 ≥5 次命中")
    void timeWindowHit() {
        var r = ev.evaluate("TIME_WINDOW",
                "{\"windowMinutes\":30,\"countThreshold\":5}", null, 6, null, null);
        assertTrue(r.hit(), r.explain());
        assertTrue(r.explain().contains("30 分钟内"), r.explain());
    }

    @Test
    @DisplayName("⭐ 时间窗：次数不足不命中")
    void timeWindowMiss() {
        var r = ev.evaluate("TIME_WINDOW",
                "{\"windowMinutes\":30,\"countThreshold\":5}", null, 4, null, null);
        assertFalse(r.hit(), r.explain());
    }

    @Test
    @DisplayName("时间窗恰等于阈值命中（>= 语义）")
    void timeWindowBoundary() {
        assertTrue(ev.evaluate("TIME_WINDOW",
                "{\"windowMinutes\":10,\"countThreshold\":3}", null, 3, null, null).hit());
    }

    // ==================== RATIO ====================

    @Test
    @DisplayName("⭐ 比例：不可信开门占比 25% ≥ 20% 命中")
    void ratioHit() {
        var r = ev.evaluate("RATIO", "{\"ratioThreshold\":0.2}",
                n("25"), null, null, n("100"));
        assertTrue(r.hit(), r.explain());
        assertTrue(r.explain().contains("%"), r.explain());
    }

    @Test
    @DisplayName("⭐ 比例：20% 恰好等于阈值命中（>=）")
    void ratioBoundary() {
        assertTrue(ev.evaluate("RATIO", "{\"ratioThreshold\":0.2}",
                n("20"), null, null, n("100")).hit());
        assertFalse(ev.evaluate("RATIO", "{\"ratioThreshold\":0.2}",
                n("19"), null, null, n("100")).hit());
    }

    @Test
    @DisplayName("⭐⭐ 分母为 0 → 不命中且不抛异常（除零保护）")
    void ratioZeroDenominator() {
        var r = ev.evaluate("RATIO", "{\"ratioThreshold\":0.2}",
                n("5"), null, null, BigDecimal.ZERO);
        assertFalse(r.hit());
        assertTrue(r.explain().contains("除零") || r.explain().contains("缺少分母"),
                r.explain());
    }

    @Test
    @DisplayName("缺分母 → 不命中，说明原因")
    void ratioNoTotal() {
        var r = ev.evaluate("RATIO", "{\"ratioThreshold\":0.2}",
                n("5"), null, null, null);
        assertFalse(r.hit());
    }

    @Test
    @DisplayName("比例默认阈值 20%")
    void ratioDefaultThreshold() {
        assertTrue(ev.evaluate("RATIO", "{}", n("25"), null, null, n("100")).hit());
        assertFalse(ev.evaluate("RATIO", "{}", n("15"), null, null, n("100")).hit());
    }

    // ==================== DURATION ====================

    @Test
    @DisplayName("⭐ 持续时长：离线 120 分钟 ≥ 60 命中")
    void durationHit() {
        var r = ev.evaluate("DURATION", "{\"durationMinutes\":60}",
                n("120"), null, null, null);
        assertTrue(r.hit(), r.explain());
    }

    @Test
    @DisplayName("持续时长不足不命中")
    void durationMiss() {
        assertFalse(ev.evaluate("DURATION", "{\"durationMinutes\":60}",
                n("59"), null, null, null).hit());
    }

    // ==================== EVENT_MATCH ====================

    @Test
    @DisplayName("⭐ 事件匹配：挟持开门在清单内 → 命中")
    void eventMatchExact() {
        var r = ev.evaluate("EVENT_MATCH",
                "{\"events\":[\"access.duress\",\"device.offline\"]}",
                null, null, "access.duress", null);
        assertTrue(r.hit(), r.explain());
    }

    @Test
    @DisplayName("⭐ 事件前缀通配：access.* 匹配 access.record")
    void eventPrefixWildcard() {
        var r = ev.evaluate("EVENT_MATCH", "{\"events\":[\"access.*\"]}",
                null, null, "access.record", null);
        assertTrue(r.hit(), r.explain());
    }

    @Test
    @DisplayName("事件不在清单 → 不命中")
    void eventNotMatched() {
        assertFalse(ev.evaluate("EVENT_MATCH", "{\"events\":[\"access.duress\"]}",
                null, null, "access.record", null).hit());
    }

    @Test
    @DisplayName("缺 events 配置 → 不命中并说明（不静默全命中）")
    void eventNoConfig() {
        var r = ev.evaluate("EVENT_MATCH", "{}", null, null, "access.duress", null);
        assertFalse(r.hit());
        assertTrue(r.explain().contains("events"), r.explain());
    }

    // ==================== 容错 ====================

    @Test
    @DisplayName("⭐ 阈值 JSON 非法 → 不命中且说明（不能因配置错把业务打挂）")
    void invalidJson() {
        var r = ev.evaluate("THRESHOLD", "not-a-json", n("100"), null, null, null);
        assertFalse(r.hit());
        assertTrue(r.explain().contains("非法 JSON"), r.explain());
    }

    @Test
    @DisplayName("未知规则类型 → 不命中并说明")
    void unknownType() {
        var r = ev.evaluate("GOLDEN_RULE", "{}", n("1"), null, null, null);
        assertFalse(r.hit());
        assertTrue(r.explain().contains("未知规则类型"), r.explain());
    }

    @Test
    @DisplayName("规则类型大小写不敏感")
    void caseInsensitive() {
        assertTrue(ev.evaluate("threshold", "{\"op\":\">\",\"value\":1}",
                n("2"), null, null, null).hit());
    }

    @Test
    @DisplayName("支持的规则类型清单完整")
    void supportedTypes() {
        assertEquals(5, ev.supportedTypes().size());
        assertTrue(ev.supportedTypes().contains("TIME_WINDOW"));
        assertTrue(ev.supportedTypes().contains("RATIO"));
    }
}
'''

ENGINE = r'''package com.yundao.bp.rule;

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
        when(logMapper.insert(any())).thenReturn(1);
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
                .insert(any());
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
'''

for rel, src in (('ThresholdEvaluatorTest.java', EVAL), ('RuleEngineTest.java', ENGINE)):
    p = os.path.join(BASE, rel)
    os.makedirs(BASE, exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  + rule/%s（%d 行）' % (rel, src.count('\n')))
