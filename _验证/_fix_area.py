# -*- coding: utf-8 -*-
"""修正：按面积计费但房源缺面积时，给明确原因"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

if '房源未录入建筑面积' in s:
    print('已修正过，跳过')
    raise SystemExit

old = '''            Integer qty = quantityOf(mode, house, nights, cmd.quantityOverride());
            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty);'''

new = '''            // 按面积计费但房源未录面积：明确跳过并给出准确原因，
            // 不能兜底成 0 再以"金额为 0"跳过（原因会误导排查）
            if (mode.needsArea() && (house == null || house.getArea() == null
                    || house.getArea().compareTo(BigDecimal.ZERO) <= 0)) {
                skipped++;
                String why = house == null ? "合同未关联房源"
                        : "房源未录入建筑面积（houseId=" + house.getId() + "）";
                skipReasons.add("合同 " + ct.getContractNo() + " 跳过：" + why);
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, null,
                        BigDecimal.ZERO, null, SKIPPED_LITERAL, why));
                continue;
            }

            Integer qty = quantityOf(mode, house, nights, cmd.quantityOverride());
            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty);'''

assert old in s, 'anchor1 missing'
s = s.replace(old, new, 1)

old2 = '''            case BY_AREA -> BillingCalculator.Context.ofArea(
                    house == null || house.getArea() == null
                            ? BigDecimal.ZERO : house.getArea());'''
new2 = '''            case BY_AREA -> BillingCalculator.Context.ofArea(house.getArea());'''
assert old2 in s, 'anchor2 missing'
s = s.replace(old2, new2, 1)

# 定义常量，避免引号转义问题
old3 = '    private static final DateTimeFormatter PERIOD_FMT = DateTimeFormatter.ofPattern("yyyy-MM");'
new3 = ('    private static final DateTimeFormatter PERIOD_FMT = DateTimeFormatter.ofPattern("yyyy-MM");\n'
        '    private static final String SKIPPED_LITERAL = "SKIPPED";')
assert old3 in s, 'anchor3 missing'
s = s.replace(old3, new3, 1)

s = s.replace(' SKIPPED_LITERAL, why));', ' SKIPPED_LITERAL, why));')

io.open(p, 'w', encoding='utf-8').write(s)
print('已修正：面积缺失给明确原因')
