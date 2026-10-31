# -*- coding: utf-8 -*-
import io

# 1) 计算器暴露“对已算金额应用规则（减免/折扣）”，供合同租金使用
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\BillingCalculator.java'
s = io.open(p, encoding='utf-8').read()
anchor = '''    /** 基础金额。 */'''
add = '''    /**
     * 对已经算好的金额套用规则（合同租金等自定义基数场景）。
     * 仅处理全额减免与折扣；阶梯/标准不改变金额。
     */
    public BigDecimal applyRuleToAmount(BigDecimal baseAmount, FinBillingRule rule) {
        BigDecimal base = baseAmount == null ? BigDecimal.ZERO : baseAmount;
        if (rule == null) {
            return base;
        }
        RuleType ruleType;
        try {
            ruleType = RuleType.valueOf(rule.getRuleType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("规则类型不合法: " + rule.getRuleType());
        }
        String config = rule.getPriceConfig() == null ? "{}" : rule.getPriceConfig();
        if (ruleType == RuleType.EXEMPT) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }
        if (ruleType == RuleType.DISCOUNT) {
            BigDecimal rate = extractRate(config);
            if (rate != null && (rate.compareTo(BigDecimal.ZERO) < 0
                    || rate.compareTo(BigDecimal.ONE) > 0)) {
                throw BizException.paramInvalid("折扣率应在 0~1 之间: " + rate);
            }
            if (rate != null) {
                return base.multiply(rate).setScale(2, RoundingMode.HALF_UP);
            }
        }
        return base;
    }

    /** 基础金额。 */'''
if 'applyRuleToAmount' not in s:
    s = s.replace(anchor, add, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('rule adjustment helper added')

# 2) 合同租金出账也套用规则
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月";'''
new = '''                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月";
                // 合同租金仍受规则约束：EXEMPT 归零、DISCOUNT 打折
                BigDecimal adjusted = calculator.applyRuleToAmount(amount, rule);
                if (adjusted.compareTo(amount) != 0) {
                    calcExplain = calcExplain + "；规则调整后 " + adjusted.toPlainString();
                    amount = money(adjusted);
                }'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('rent applies rule')

# 3) 抄表：同日多次读数取最近一条（原逻辑只看更早日期，会重复计费）
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\MeterReadingServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''                .lt(FinMeterReading::getReadDate, readDate)
                .orderByDesc(FinMeterReading::getReadDate)'''
new = '''                .le(FinMeterReading::getReadDate, readDate)
                .orderByDesc(FinMeterReading::getReadDate)
                .orderByDesc(FinMeterReading::getId)'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('meter same-day reading fixed')

# 4) 退租结算：退款不能超过当前押金余额
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\TerminationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''        BigDecimal refund = depositRefund == null
                ? (java.math.BigDecimal) auto.get("depositAmount") : depositRefund;
        BigDecimal arrears = arrearsAmount == null
                ? (java.math.BigDecimal) auto.get("arrearsAmount") : arrearsAmount;'''
new = '''        BigDecimal refund = depositRefund == null
                ? (java.math.BigDecimal) auto.get("depositAmount") : depositRefund;
        BigDecimal arrears = arrearsAmount == null
                ? (java.math.BigDecimal) auto.get("arrearsAmount") : arrearsAmount;
        java.math.BigDecimal available = (java.math.BigDecimal) auto.get("depositAmount");
        if (refund.compareTo(java.math.BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("应退押金不能为负");
        }
        if (available != null && refund.compareTo(available) > 0) {
            throw BizException.paramInvalid("应退押金不能超过押金余额 " + available);
        }
        if (arrears.compareTo(java.math.BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("欠费金额不能为负");
        }'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('settlement refund cap added')
