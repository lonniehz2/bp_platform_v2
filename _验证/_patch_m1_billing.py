# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

# imports
s = s.replace('import com.yundao.bp.biz.mapper.BizContractMapper;',
              'import com.yundao.bp.biz.entity.BizContractCohabitant;\n'
              'import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;\n'
              'import com.yundao.bp.biz.mapper.BizContractMapper;', 1)
s = s.replace('import java.util.ArrayList;\nimport java.util.List;',
              'import java.util.ArrayList;\nimport java.util.Comparator;\nimport java.util.List;\n'
              'import java.util.Map;\nimport java.util.LinkedHashMap;', 1)

# fields
s = s.replace('''    private final FinBillMapper billMapper;
    private final BillingCalculator calculator;''',
              '''    private final FinBillMapper billMapper;
    private final BizContractCohabitantMapper cohabitantMapper;
    private final BillingCalculator calculator;''', 1)

s = s.replace('''                                     FinBillingRuleMapper ruleMapper,
                                     FinBillMapper billMapper,
                                     BillingCalculator calculator,
                                     SnowflakeIdGenerator idGen) {''',
              '''                                     FinBillingRuleMapper ruleMapper,
                                     FinBillMapper billMapper,
                                     BizContractCohabitantMapper cohabitantMapper,
                                     BillingCalculator calculator,
                                     SnowflakeIdGenerator idGen) {''', 1)
s = s.replace('''        this.billMapper = billMapper;
        this.calculator = calculator;''',
              '''        this.billMapper = billMapper;
        this.cohabitantMapper = cohabitantMapper;
        this.calculator = calculator;''', 1)

# 规则加载：手动 + 自动候选
old = '''        FinBillingRule rule = null;
        if (cmd.ruleId() != null) {
            rule = ruleMapper.selectById(cmd.ruleId());
            if (rule == null) {
                throw BizException.notFound("计费规则");
            }
            if (!"APPROVED".equals(rule.getApproveStatus())) {
                throw BizException.stateConflict("规则未审批通过，不能用于计费");
            }
        }'''
new = '''        String ruleMode = cmd.ruleMode() == null || cmd.ruleMode().isBlank()
                ? (cmd.ruleId() != null ? "MANUAL" : "AUTO")
                : cmd.ruleMode().trim().toUpperCase();
        if (!List.of("AUTO", "MANUAL", "NONE").contains(ruleMode)) {
            throw BizException.paramInvalid("规则方式不合法: " + cmd.ruleMode());
        }
        FinBillingRule manualRule = null;
        if ("MANUAL".equals(ruleMode)) {
            if (cmd.ruleId() == null) {
                throw BizException.paramInvalid("指定规则时必须选择计费规则");
            }
            manualRule = ruleMapper.selectById(cmd.ruleId());
            if (manualRule == null) {
                throw BizException.notFound("计费规则");
            }
            if (!"APPROVED".equals(manualRule.getApproveStatus())) {
                throw BizException.stateConflict("规则未审批通过，不能用于计费");
            }
        }
        // 自动匹配候选：只取本项目、已启用、已审批的规则
        List<FinBillingRule> candidates = new ArrayList<>();
        if ("AUTO".equals(ruleMode)) {
            candidates = ruleMapper.selectList(new LambdaQueryWrapper<FinBillingRule>()
                    .eq(FinBillingRule::getFeeItemId, cmd.feeItemId())
                    .eq(FinBillingRule::getStatus, "ENABLED")
                    .eq(FinBillingRule::getApproveStatus, "APPROVED")
                    .eq(FinBillingRule::getIsDeleted, 0));
        }'''
if old not in s:
    raise SystemExit('rule block not found')
s = s.replace(old, new, 1)

# 账单周期规范化
s = s.replace('''        String billPeriod = cmd.billPeriod() == null || cmd.billPeriod().isBlank()
                ? cmd.periodStart().format(PERIOD_FMT) : cmd.billPeriod();''',
              '''        String billPeriod = normalizePeriod(cmd.billPeriod(), cmd.periodStart());''', 1)

# 循环内规则解析
s = s.replace('''            AssetHouse house = ct.getHouseId() == null ? null
                    : houseMapper.selectById(ct.getHouseId());
''',
              '''            AssetHouse house = ct.getHouseId() == null ? null
                    : houseMapper.selectById(ct.getHouseId());
            FinBillingRule effectiveRule = "NONE".equals(ruleMode) ? null
                    : ("MANUAL".equals(ruleMode) ? manualRule
                    : matchRule(candidates, ct, house, cmd.periodStart(), cmd.periodEnd()));
''', 1)

# 数量：按合同实际人口/床位
s = s.replace('Integer qty = quantityOf(mode, house, nights, cmd.quantityOverride());',
              'Integer qty = quantityOf(mode, ct, house, nights, cmd.quantityOverride());', 1)
s = s.replace('Integer qty = quantityOf(mode, house, 0, null);',
              'Integer qty = quantityOf(mode, ct, house, 0, null);', 2)

# 计算与租金规则
s = s.replace('rr = calculator.calculate(item, ctx, rule);',
              'rr = calculator.calculate(item, ctx, effectiveRule);', 1)
s = s.replace('BigDecimal adjusted = calculator.applyRuleToAmount(amount, rule);',
              'BigDecimal adjusted = calculator.applyRuleToAmount(amount, effectiveRule);', 1)
s = s.replace('''                calcExplain = "合同月租 "''','''                calcExplain = "合同月租 "''', 1)

# 账单写规则与数量快照
s = s.replace('''                b.setGenerateType("AUTO");''',
              '''                b.setGenerateType("AUTO");
                b.setRuleId(effectiveRule == null ? null : effectiveRule.getId());
                b.setRuleVersion(effectiveRule == null ? null : effectiveRule.getRuleVersion());
                b.setRuleSnapshot(snapshot(effectiveRule));
                b.setBillingQuantity(qty);
                b.setQuantityUnit(quantityUnit(mode));
                b.setQuantitySource(quantitySource(mode));''', 1)

# 说明补充规则
s = s.replace('''                b.setRemark("批量出账：" + item.getItemName() + "；" + pro.detail()''',
              '''                b.setRemark("批量出账：" + item.getItemName()
                        + (effectiveRule == null ? "" : "（规则：" + effectiveRule.getRuleName() + "）")
                        + "；" + pro.detail()''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('bill generation M1 patched')
