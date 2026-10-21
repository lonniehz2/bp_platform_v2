package com.yundao.bp.rule;

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
