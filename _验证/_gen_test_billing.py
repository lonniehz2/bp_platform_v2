# -*- coding: utf-8 -*-
"""生成 BillingCalculator 单元测试（7 计费方式 × 4 规则类型 + 边界）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\fin'
os.makedirs(BASE, exist_ok=True)

SRC = r'''package com.yundao.bp.fin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.service.BillingCalculator;
import java.math.BigDecimal;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 计费引擎单元测试。
 *
 * <p><b>为什么这批测试最重要</b>：计费直接决定向住户收多少钱，
 * 算错就是真实的钱错。且它是纯函数（无数据库、无 Spring），
 * 可以用最便宜的方式覆盖全部组合。
 *
 * <p>覆盖矩阵：<b>7 种计费方式 × 4 类规则类型</b>，外加参数缺失与边界。
 */
class BillingCalculatorTest {

    private final BillingCalculator calc = new BillingCalculator();

    // ==================== 构造辅助 ====================

    private static FinFeeItem item(CalcMode mode, String unitPrice) {
        FinFeeItem i = new FinFeeItem();
        i.setCalcMode(mode.name());
        i.setUnitPrice(new BigDecimal(unitPrice));
        i.setItemType("RENT");
        i.setStatus("ENABLED");
        return i;
    }

    private static FinBillingRule rule(com.yundao.bp.fin.constant.RuleType type, String json) {
        FinBillingRule r = new FinBillingRule();
        r.setRuleType(type.name());
        r.setPriceConfig(json);
        r.setApproveStatus("APPROVED");
        return r;
    }

    private static void assertMoney(String expect, BigDecimal actual) {
        assertEquals(0, new BigDecimal(expect).compareTo(actual),
                "期望 " + expect + "，实际 " + actual);
    }

    // ==================== 一、7 种计费方式 ====================

    @Test
    @DisplayName("FIXED 固定额：物业费 150 → 150.00")
    void fixed() {
        var r = calc.calculate(item(CalcMode.FIXED, "150"), BillingCalculator.Context.empty());
        assertMoney("150.00", r.finalAmount());
        assertMoney("150.00", r.baseAmount());
    }

    @Test
    @DisplayName("BY_AREA 按面积：89.5㎡ × 12.50 = 1118.75（保障房租金）")
    void byArea() {
        var r = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("89.5")));
        assertMoney("1118.75", r.finalAmount());
        assertTrue(r.explain().contains("按面积"), r.explain());
    }

    @Test
    @DisplayName("BY_HOUSE 按套：整套 1000 → 1000.00")
    void byHouse() {
        var r = calc.calculate(item(CalcMode.BY_HOUSE, "1000"),
                BillingCalculator.Context.empty());
        assertMoney("1000.00", r.finalAmount());
    }

    @Test
    @DisplayName("BY_PERSON 按人：300 × 3 人 = 900.00")
    void byPerson() {
        var r = calc.calculate(item(CalcMode.BY_PERSON, "300"),
                BillingCalculator.Context.ofQuantity(3));
        assertMoney("900.00", r.finalAmount());
    }

    @Test
    @DisplayName("BY_BED 按床位：300 × 4 床 = 1200.00（宿舍业态）")
    void byBed() {
        var r = calc.calculate(item(CalcMode.BY_BED, "300"),
                BillingCalculator.Context.ofQuantity(4));
        assertMoney("1200.00", r.finalAmount());
    }

    @Test
    @DisplayName("BY_NIGHT 按夜：288 × 3 夜 = 864.00（民宿业态）")
    void byNight() {
        var r = calc.calculate(item(CalcMode.BY_NIGHT, "288"),
                BillingCalculator.Context.ofQuantity(3));
        assertMoney("864.00", r.finalAmount());
    }

    @Test
    @DisplayName("METER 按抄表：(1150-1000) 度 × 0.65 = 97.50（园区能耗）")
    void meter() {
        var r = calc.calculate(item(CalcMode.METER, "0.65"),
                BillingCalculator.Context.ofMeter(new BigDecimal("1000"),
                        new BigDecimal("1150")));
        assertMoney("97.50", r.finalAmount());
    }

    // ==================== 二、4 类规则类型 ====================

    @Test
    @DisplayName("STANDARD 标准价：规则价覆盖项目单价（100㎡ × 10 = 1000.00）")
    void ruleStandard() {
        var r = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("100")),
                rule(com.yundao.bp.fin.constant.RuleType.STANDARD,
                        "{\"price\": 10.00}"));
        assertMoney("1000.00", r.finalAmount());
    }

    @Test
    @DisplayName("DISCOUNT 折扣：150 × 0.9 = 135.00")
    void ruleDiscount() {
        var r = calc.calculate(item(CalcMode.FIXED, "150"),
                BillingCalculator.Context.empty(),
                rule(com.yundao.bp.fin.constant.RuleType.DISCOUNT, "{\"rate\": 0.9}"));
        assertMoney("135.00", r.finalAmount());
        assertMoney("150.00", r.baseAmount());
    }

    @Test
    @DisplayName("EXEMPT 减免：全额归零 0.00（廉租全免）")
    void ruleExempt() {
        var r = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("100")),
                rule(com.yundao.bp.fin.constant.RuleType.EXEMPT, "{}"));
        assertMoney("0.00", r.finalAmount());
    }

    @Test
    @DisplayName("TIERED 阶梯：150 度 = 50×0.5 + 100×0.8 = 105.00（分段累加）")
    void ruleTiered() {
        var r = calc.calculate(item(CalcMode.METER, "0.65"),
                BillingCalculator.Context.ofMeter(BigDecimal.ZERO,
                        new BigDecimal("150")),
                rule(com.yundao.bp.fin.constant.RuleType.TIERED,
                        "{\"tiers\":[{\"limit\":50,\"price\":0.50},"
                                + "{\"limit\":null,\"price\":0.80}]}"));
        assertMoney("105.00", r.finalAmount());
    }

    @Test
    @DisplayName("TIERED 阶梯：30 度只落第一档 = 15.00")
    void ruleTieredFirstTierOnly() {
        var r = calc.calculate(item(CalcMode.METER, "0.65"),
                BillingCalculator.Context.ofMeter(BigDecimal.ZERO,
                        new BigDecimal("30")),
                rule(com.yundao.bp.fin.constant.RuleType.TIERED,
                        "{\"tiers\":[{\"limit\":50,\"price\":0.50},"
                                + "{\"limit\":null,\"price\":0.80}]}"));
        assertMoney("15.00", r.finalAmount());
    }

    @Test
    @DisplayName("TIERED 阶梯：恰好等于第一档上限 50 度 = 25.00（不多算）")
    void ruleTieredBoundary() {
        var r = calc.calculate(item(CalcMode.METER, "0.65"),
                BillingCalculator.Context.ofMeter(BigDecimal.ZERO,
                        new BigDecimal("50")),
                rule(com.yundao.bp.fin.constant.RuleType.TIERED,
                        "{\"tiers\":[{\"limit\":50,\"price\":0.50},"
                                + "{\"limit\":null,\"price\":0.80}]}"));
        assertMoney("25.00", r.finalAmount());
    }

    // ==================== 三、金额精度 ====================

    @Test
    @DisplayName("精度：结果统一 2 位小数 HALF_UP（89.5×12.505 = 1119.20）")
    void rounding() {
        var r = calc.calculate(item(CalcMode.BY_AREA, "12.505"),
                BillingCalculator.Context.ofArea(new BigDecimal("89.5")));
        // 89.5 × 12.505 = 1119.1975 → HALF_UP 2 位 = 1119.20
        assertMoney("1119.20", r.finalAmount());
        assertEquals(2, r.finalAmount().scale(), "必须固定 2 位小数");
    }

    @Test
    @DisplayName("精度：整数结果也补 2 位（300 → 300.00，前端不走样）")
    void integerScale() {
        var r = calc.calculate(item(CalcMode.FIXED, "300"),
                BillingCalculator.Context.empty());
        assertEquals("300.00", r.finalAmount().toPlainString());
    }

    // ==================== 四、参数缺失（必须明确报错，不能算成 0） ====================

    @Test
    @DisplayName("BY_AREA 缺面积 → 报错（不能静默算成 0）")
    void byAreaMissingArea() {
        BizException ex = assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                        BillingCalculator.Context.empty()));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("面积"), ex.getMessage());
    }

    @Test
    @DisplayName("BY_PERSON 缺数量 → 报错")
    void byPersonMissingQuantity() {
        BizException ex = assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.BY_PERSON, "300"),
                        BillingCalculator.Context.empty()));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("数量为 0 → 报错（0 人不应产生 0 元账单）")
    void zeroQuantity() {
        BizException ex = assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.BY_BED, "300"),
                        BillingCalculator.Context.ofQuantity(0)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("METER 本次读数小于上次 → 报错（换表/回滚场景需人工处理）")
    void meterReversed() {
        BizException ex = assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.METER, "0.65"),
                        BillingCalculator.Context.ofMeter(new BigDecimal("2000"),
                                new BigDecimal("1000"))));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("读数"), ex.getMessage());
    }

    @Test
    @DisplayName("METER 缺读数 → 报错")
    void meterMissing() {
        assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.METER, "0.65"),
                        BillingCalculator.Context.empty()));
    }

    @Test
    @DisplayName("收费项目为空 → 报错")
    void nullItem() {
        assertThrows(BizException.class,
                () -> calc.calculate(null, BillingCalculator.Context.empty()));
    }

    @Test
    @DisplayName("非法计费方式 → 报错")
    void invalidCalcMode() {
        FinFeeItem bad = item(CalcMode.FIXED, "1");
        bad.setCalcMode("BY_WHATEVER");
        assertThrows(BizException.class,
                () -> calc.calculate(bad, BillingCalculator.Context.empty()));
    }

    @Test
    @DisplayName("非法规则类型 → 报错")
    void invalidRuleType() {
        FinBillingRule bad = new FinBillingRule();
        bad.setRuleType("GOLDEN");
        bad.setPriceConfig("{}");
        assertThrows(BizException.class,
                () -> calc.calculate(item(CalcMode.FIXED, "1"),
                        BillingCalculator.Context.empty(), bad));
    }

    // ==================== 五、规则容错 ====================

    @Test
    @DisplayName("价格配置非法 JSON → 回退项目默认单价（不因配置错导致无法出账）")
    void malformedConfigFallsBack() {
        var r = calc.calculate(item(CalcMode.FIXED, "150"),
                BillingCalculator.Context.empty(),
                rule(com.yundao.bp.fin.constant.RuleType.STANDARD, "not-a-json"));
        assertMoney("150.00", r.finalAmount());
    }

    @Test
    @DisplayName("阶梯配置缺 tiers → 回退基础单价计算")
    void tieredWithoutTiers() {
        var r = calc.calculate(item(CalcMode.METER, "0.65"),
                BillingCalculator.Context.ofMeter(BigDecimal.ZERO, new BigDecimal("100")),
                rule(com.yundao.bp.fin.constant.RuleType.TIERED, "{}"));
        assertMoney("65.00", r.finalAmount());
    }

    @Test
    @DisplayName("不传规则 = 等价 STANDARD（项目默认单价）")
    void noRuleEqualsStandard() {
        var withNull = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("80")), null);
        var plain = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("80")));
        assertMoney("1000.00", withNull.finalAmount());
        assertEquals(0, withNull.finalAmount().compareTo(plain.finalAmount()));
    }

    @Test
    @DisplayName("计算过程 explain 非空（审计/前端展示需要）")
    void explainPresent() {
        var r = calc.calculate(item(CalcMode.BY_AREA, "12.50"),
                BillingCalculator.Context.ofArea(new BigDecimal("100")));
        assertNotNull(r.explain());
        assertTrue(r.explain().contains("12.5"), r.explain());
    }
}
'''

path = os.path.join(BASE, 'BillingCalculatorTest.java')
io.open(path, 'w', encoding='utf-8').write(SRC)
print('已生成 %s' % path)
print('  行数 %d' % SRC.count('\n'))
