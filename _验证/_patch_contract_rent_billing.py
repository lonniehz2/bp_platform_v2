# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

old = '''            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty)
                    .withMonths(pro.months());
            BillingCalculator.Result rr;
            try {
                rr = calculator.calculate(item, ctx, rule);
            } catch (Exception e) {
                skipped++;
                skipReasons.add("合同 " + ct.getContractNo() + " 算费失败：" + e.getMessage());
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        BigDecimal.ZERO, null, "SKIPPED", e.getMessage()));
                continue;
            }

            BigDecimal amount = rr.finalAmount();
            if (amount.compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        amount, rr.explain(), "SKIPPED", "金额为 0（减免规则或数量为 0）"));
                continue;
            }
'''

new = '''            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty)
                    .withMonths(pro.months());

            // 租金类项目：以合同月租为准，不再套用收费项目里的默认单价；
            // 合同月补贴作为减免，账单应收=月租×月数，减免=补贴×月数，待缴=差额。
            BigDecimal amount;
            BigDecimal discount = money(null);
            String calcExplain;
            if ("RENT".equals(item.getItemType())
                    && ct.getMonthlyRent() != null
                    && ct.getMonthlyRent().compareTo(BigDecimal.ZERO) > 0) {
                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                BigDecimal subsidy = ct.getSubsidyAmount() == null
                        ? BigDecimal.ZERO : ct.getSubsidyAmount();
                discount = money(subsidy.multiply(pro.months()));
                if (discount.compareTo(amount) > 0) {
                    discount = amount;
                }
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月"
                        + (discount.compareTo(BigDecimal.ZERO) > 0
                        ? "；补贴抵扣 " + discount.toPlainString() : "");
            } else {
                BillingCalculator.Result rr;
                try {
                    rr = calculator.calculate(item, ctx, rule);
                } catch (Exception e) {
                    skipped++;
                    skipReasons.add("合同 " + ct.getContractNo() + " 算费失败：" + e.getMessage());
                    items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                            BigDecimal.ZERO, null, "SKIPPED", e.getMessage()));
                    continue;
                }
                amount = rr.finalAmount();
                calcExplain = rr.explain();
            }

            BigDecimal payable = amount.subtract(discount);
            if (amount.compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        amount, calcExplain, "SKIPPED", "金额为 0（减免规则或数量为 0）"));
                continue;
            }
'''

if old not in s:
    raise SystemExit('calc block not found')
s = s.replace(old, new, 1)

s = s.replace('''                b.setBillAmount(amount);
                b.setDiscountAmount(money(null));''',
              '''                b.setBillAmount(amount);
                b.setDiscountAmount(discount);''', 1)
s = s.replace('''                b.setPayableAmount(amount);''',
              '''                b.setPayableAmount(payable);''', 1)
s = s.replace('''                b.setRemark("批量出账：" + item.getItemName() + "；" + pro.detail());''',
              '''                b.setRemark("批量出账：" + item.getItemName() + "；" + pro.detail()
                        + (discount.compareTo(BigDecimal.ZERO) > 0
                        ? "；补贴抵扣 " + discount.toPlainString() : ""));''', 1)

# 结果与合计按待缴口径返回，试运行与落库一致
s = s.replace('''            generated++;
            total = total.add(amount);
            String explain = pro.detail().isEmpty()
                    ? rr.explain() : rr.explain() + "；" + pro.detail();
            items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), billId, qty,
                    amount, explain, "OK", null));''',
'''            generated++;
            total = total.add(payable);
            String explain = pro.detail().isEmpty()
                    ? calcExplain : calcExplain + "；" + pro.detail();
            items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), billId, qty,
                    payable, explain, "OK", null));''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('bill generation uses contract rent and subsidy')
