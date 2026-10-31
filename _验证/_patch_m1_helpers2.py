# -*- coding: utf-8 -*-
import io
import re

p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

# 构造参数补 ruleMode
s = s.replace('''                GenerateResultVO one = generate(new GenerateBillsCmd(
                        it.feeItemId(), it.ruleId(),
                        cmd.periodStart(), cmd.periodEnd(),''',
              '''                GenerateResultVO one = generate(new GenerateBillsCmd(
                        it.feeItemId(), it.ruleId(), null,
                        cmd.periodStart(), cmd.periodEnd(),''', 1)

helpers = '''/** 数量取值：按合同实际保障人口/实际床位，不再取房源 maxCapacity。 */
private Integer quantityOf(CalcMode mode, BizContract ct, AssetHouse house, int nights,
                           Integer override) {
    if (override != null && override > 0) {
        return override;
    }
    return switch (mode) {
        case BY_NIGHT -> nights;
        case BY_PERSON -> personCount(ct);
        case BY_BED -> bedCount(ct);
        case FIXED, BY_HOUSE, BY_AREA -> 1;
        case METER -> 1;
    };
}

/** 保障人口 = 承租人 1 + 同住人。 */
private int personCount(BizContract ct) {
    if (ct == null || ct.getId() == null) {
        return 1;
    }
    Long n = cohabitantMapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
            .eq(BizContractCohabitant::getContractId, ct.getId()));
    return 1 + (n == null ? 0 : n.intValue());
}

/** 实际签约床位数，默认 1。 */
private static int bedCount(BizContract ct) {
    return ct != null && ct.getBillingBedCount() != null && ct.getBillingBedCount() > 0
            ? ct.getBillingBedCount() : 1;
}

private static String quantityUnit(CalcMode mode) {
    return switch (mode) {
        case BY_PERSON -> "PERSON";
        case BY_BED -> "BED";
        case BY_NIGHT -> "NIGHT";
        case BY_AREA -> "AREA";
        default -> "HOUSE";
    };
}

private static String quantitySource(CalcMode mode) {
    return switch (mode) {
        case BY_PERSON -> "COHABITANT";
        case BY_BED -> "CONTRACT";
        default -> "DEFAULT";
    };
}

/** 自动匹配规则：组织/房源类型/保障类型/生效期/优先级。 */
private static FinBillingRule matchRule(List<FinBillingRule> rules, BizContract ct,
                                        AssetHouse house, LocalDate ps, LocalDate pe) {
    if (rules == null || rules.isEmpty()) {
        return null;
    }
    String houseType = house == null ? null : house.getHouseType();
    String security = securityTypeOf(ct.getContractType());
    FinBillingRule best = null;
    int bestScore = Integer.MIN_VALUE;
    for (FinBillingRule r : rules) {
        if (r.getOrgId() != null && !r.getOrgId().equals(ct.getOrgId())) {
            continue;
        }
        if (r.getHouseType() != null && !r.getHouseType().isBlank()
                && !r.getHouseType().equals(houseType)) {
            continue;
        }
        if (r.getSecurityType() != null && !r.getSecurityType().isBlank()
                && !r.getSecurityType().equals(security)) {
            continue;
        }
        // 合同暂无收入档数据：规则限定收入档时不参与自动匹配，避免误用
        if (r.getIncomeLevel() != null && !r.getIncomeLevel().isBlank()) {
            continue;
        }
        if (r.getEffectiveStart() != null && r.getEffectiveStart().isAfter(ps)) {
            continue;
        }
        if (r.getEffectiveEnd() != null && r.getEffectiveEnd().isBefore(pe)) {
            continue;
        }
        int score = (r.getOrgId() == null ? 0 : 100)
                + (r.getSecurityType() == null || r.getSecurityType().isBlank() ? 0 : 20)
                + (r.getHouseType() == null || r.getHouseType().isBlank() ? 0 : 10)
                + (r.getPriority() == null ? 0 : r.getPriority());
        if (score > bestScore) {
            best = r;
            bestScore = score;
        }
    }
    return best;
}

private static String securityTypeOf(String contractType) {
    if (contractType == null) {
        return "PUBLIC";
    }
    if (contractType.contains("PUBLIC")) {
        return "PUBLIC";
    }
    if (contractType.contains("LOW")) {
        return "LOW";
    }
    return contractType;
}

/** 规则快照：规则后续修改不影响历史账单解释。 */
private static String snapshot(FinBillingRule r) {
    if (r == null) {
        return null;
    }
    try {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", r.getId());
        m.put("code", r.getRuleCode());
        m.put("name", r.getRuleName());
        m.put("version", r.getRuleVersion());
        m.put("type", r.getRuleType());
        m.put("config", r.getPriceConfig());
        m.put("priority", r.getPriority());
        return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(m);
    } catch (Exception e) {
        return "{}";
    }
}

/** 账期统一为 yyyy-MM（兼容前端传入 yyyyMM）。 */
private static String normalizePeriod(String period, LocalDate start) {
    if (period == null || period.isBlank()) {
        return start.format(PERIOD_FMT);
    }
    String p = period.trim().replace("/", "-");
    if (p.matches("\\\\d{6}")) {
        return p.substring(0, 4) + "-" + p.substring(4);
    }
    if (p.matches("\\\\d{4}-\\\\d{2}")) {
        return p;
    }
    return start.format(PERIOD_FMT);
}

'''

start = s.find('/** 数量取值。 */')
end = s.find('/** 构造计算上下文。 */')
if start < 0 or end < 0 or end <= start:
    raise SystemExit('quantity block not found')
s = s[:start] + helpers + s[end:]

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('helpers inserted')
